import base64
import json
from pathlib import Path

import requests

from config import settings
from database.database import Condition, DatabaseConnection
from utils.handle_files import HandleFiles


class ProcessMessages:
    def __init__(self, base_url, input_folder, output_folder, headers) -> None:
        self.service_url = f'https://{base_url}/ChangeQueuedToProcessed'
        self.headers = headers
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)

    def update_message(self, sender, receiver, message_id) -> None:  # noqa: PLR6301
        payload = {
            'Sender': sender,
            'Receiver': receiver,
            'MessageId': message_id,
        }

        request = json.dumps(payload)

        response = requests.post(self.service_url, headers=self.headers, data=request)

        json_response = json.loads(response.text)  # noqa: F841

    def create_orders_files(self, messages_data) -> None:  # noqa: PLR6301
        for message in messages_data:
            base64_string = message['ResultData']['Base64Data']
            content_type = message['ResultData']['ContentType']
            file_name = message['ResultData']['Filename']
            message_id = message['ResultData']['MessageId']
            receiver = message['ResultData']['Receiver']
            sender = message['ResultData']['Sender']

            if content_type == 'text/plain':
                file_to_copy = self.create_text_order_file(base64_string, file_name)

                # Atualizar a mensagem para processada
                self.update_message(sender, receiver, message_id)

                # Copiar o ficheiro gerado para a pasta final com novo nome
                new_file_name = f'{self.get_new_order_number()}.txt'

                if new_file_name:
                    handle_files = HandleFiles(self.input_folder, self.output_folder)
                    handle_files.copy_file(file_to_copy, new_file_name, metadata=False)

    def create_text_order_file(self, base64_string, filename) -> str:
        # Decodificar a string
        decoded_bytes = base64.b64decode(base64_string)

        # Salvar em um ficheiro de texto
        save_filename = self.input_folder / filename

        with open(save_filename, 'wb') as file:
            file.write(decoded_bytes)

        return save_filename

    def get_new_order_number() -> str:
        # Conectar ao banco de dados
        with DatabaseConnection(
            settings.DB_SERVER,
            settings.DB_DATABASE,
            settings.DB_USERNAME,
            settings.DB_PASSWORD,
        ) as db:
            # Executar a query para obter o próximo número
            result_query = db.execute_query(
                table=f'{settings.DB_SCHEMA}.AVALNUM',
                columns=['VALEUR_0', 'ROWID'],
                where_clauses={'CODNUM_0': ('=', 'ZLO')},
            )

            # Recuperar o resultado
            if result_query['status'] == 'success':
                sequence = int(result_query['data'][0]['VALEUR_0'])
                row_id = int(result_query['data'][0]['ROWID'])

                # Incrementar o número
                sequence += 1

                # Atualizar o número na base de dados
                result = db.execute_update(
                    table_name=f'{settings.DB_SCHEMA}.AVALNUM',
                    set_columns={'VALEUR_0': sequence},
                    where_clauses={'ROWID': Condition('=', row_id)},
                )

                if result['status'] == 'success':
                    return f'ORD{sequence:07}'
                else:
                    return ''
