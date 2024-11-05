from typing import Any, Dict, Optional, Tuple

import pyodbc

from database.condition import Condition
from utils.conversions import Conversions


class DatabaseConnection:
    def __init__(self, server, database, username, password):
        self.validate_params(server, database, username, password)
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None

    @staticmethod
    def build_connection_string(server, database, username, password):
        return (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )

    @staticmethod
    def validate_params(server, database, username, password):
        if not server or not database or not username or not password:
            raise ValueError('All connection parameters must be provided.')

    def connect(self):
        try:
            connection_string = self.build_connection_string(
                self.server, self.database, self.username, self.password
            )
            self.connection = pyodbc.connect(connection_string)
            return {'status': 'success', 'message': 'Connection successful'}
        except pyodbc.Error as e:
            return {'status': 'error', 'message': f'Error connecting to database: {e}'}

    def disconnect(self):
        if self.connection:
            self.connection.close()
            return {'status': 'success', 'message': 'Connection closed'}

        return {'status': 'info', 'message': 'No active connection to close'}

    def execute_query(
        self,
        table: str,
        columns: Optional[list[str]] = None,
        where_clauses: Optional[Dict[str, Tuple[str, Any]]] = None,
        group_by: Optional[str] = None,
        order_by: Optional[str] = None,
    ):
        # Check if there is an active connection
        if not self.connection:
            try:
                self.connect()
            except Exception:
                return {
                    'status': 'error',
                    'message': 'No active connection',
                    'data': None,
                }

        # Build the SELECT clause dynamically
        select_clause = ', '.join(columns) if columns else '*'

        query = f'SELECT {select_clause} FROM {table}'

        # Build the WHERE clause dynamically with multiple conditions
        if where_clauses:
            where_clause = ' AND '.join([
                f'{column} {operator} ?'
                for column, (operator, _) in where_clauses.items()
            ])
            query += f' WHERE {where_clause}'
            where_values = tuple(value for _, value in where_clauses.values())
        else:
            where_values = ()

        # Add GROUP BY clause if provided
        if group_by:
            query += f' GROUP BY {group_by}'

        # Add ORDER BY clause if provided
        if order_by:
            query += f' ORDER BY {order_by}'

        try:
            with self.connection.cursor() as cursor:
                # Execute the query with the WHERE values if any are provided
                cursor.execute(query, where_values)

                # Get the column names from the cursor description
                columns_names = [column[0] for column in cursor.description]

                # Fetch all results and build a list of dictionaries
                results = [
                    {
                        columns_names[index]: row[index]
                        for index in range(len(columns_names))
                    }
                    for row in cursor.fetchall()
                ]

                return {
                    'status': 'success',
                    'message': 'Query executed successfully',
                    'columns': columns_names,
                    'data': results,
                }
        except pyodbc.Error as e:
            return {
                'status': 'error',
                'message': f'Error executing query: {e}',
                'data': None,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {e}',
                'data': None,
            }

    def execute_update(
        self,
        table_name: str,
        set_columns: Dict[str, Any],
        where_clauses: Dict[str, Condition],
    ) -> Dict[str, str]:
        """
        Atualiza registros em uma tabela específica do banco de dados com múltiplas
        condições no WHERE.

        Parâmetros:
        - table_name (str): nome da tabela a ser atualizada.
        - set_columns (dict): dicionário onde as chaves são as colunas e os valores são os novos
          dados a serem atualizados.
        - where_conditions (dict): dicionário onde as chaves são as colunas e os valores são são instâncias
          da classe Condition, representando as condições para cada campo.

        Retorno:

        dict: Um dicionário contendo informações sobre o resultado da operação, como status (sucesso ou erro),
          mensagem e dados adicionais (se houver).

        Exemplo de uso:
        # Criando instâncias de Condition
        condition1 = Condition("=", "valor1")
        condition2 = Condition(">", 10)

        update_table("Customers", {"Name": "John", "Age": 30}, {"ID": 1, "Campo 1": condition1, "Campo 2": condition2})
        """  # noqa: E501

        # Check if there is an active connection
        if not self.connection:
            try:
                self.connect()
            except pyodbc.Error:
                return {
                    'status': 'error',
                    'message': 'No active connection: {e}',
                    'data': None,
                }

        # Check if the SET columns and WHERE conditions are provided
        if not isinstance(set_columns, dict) or not isinstance(where_clauses, dict):
            return {
                'status': 'error',
                'message': (
                    'SET columns and WHERE conditions must be provided as dictionaries'
                ),
                'data': None,
            }

        # Build the SET clause dynamically with placeholders
        set_clause = ', '.join([f'{column} = ?' for column in set_columns.keys()])

        # Build the WHERE clause dynamically with multiple conditions
        where_clause_parts = []
        values = list(set_columns.values())

        for column, condition in where_clauses.items():
            # Check if the condition is an instance of the Condition class
            if not isinstance(condition, Condition):
                return {
                    'status': 'error',
                    'message': (
                        'Invalid condition for column {column}.'
                        'Must be instances of the Condition class'
                    ),
                    'data': None,
                }

            # Add the condition to the WHERE clause
            where_clause_parts.append(f'{column} {condition.operator} ?')
            values.append(Conversions.convert_value(condition.value))

        # Join the WHERE clause parts with AND
        where_clause = ' AND '.join(where_clause_parts)

        # Build the query with the SET and WHERE clauses
        query = f'UPDATE {table_name} SET {set_clause} WHERE {where_clause}'

        # Check if number of placeholders matches the number of values
        expected_placeholders = len(set_columns) + len(where_clauses)

        if len(values) != expected_placeholders:
            return {
                'status': 'error',
                'message': (
                    f'Number of values does not match the number of placeholders.'
                    f'Expected {expected_placeholders} values, got {len(values)}'
                ),
                'data': None,
            }

        try:
            with self.connection.cursor() as cursor:
                # Execute the query with the WHERE values if any are provided
                cursor.execute(query, values)
                self.connection.commit()

                return {
                    'status': 'success',
                    'message': 'Update executed successfully',
                }
        except pyodbc.Error as e:
            return {
                'status': 'error',
                'message': f'Error executing query: {e}',
                'data': None,
            }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f'Exception: {exc_type}')
            print(f'Exception: {exc_value}')

        self.disconnect()
