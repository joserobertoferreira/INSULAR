import base64
import json
import uuid
from datetime import datetime, timezone
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
                new_file_name = self.get_new_order_number()

                if new_file_name:
                    handle_files = HandleFiles(self.input_folder, self.output_folder)
                    handle_files.copy_file(
                        file_to_copy, f'{new_file_name}.txt', metadata=False
                    )

                    # Atualizar tabela de log com o novo nome do ficheiro
                    self.update_log_table(
                        self.input_folder,
                        self.output_folder,
                        file_to_copy,
                        new_file_name,
                    )

    def create_text_order_file(self, base64_string, filename) -> str:
        # Decodificar a string
        decoded_bytes = base64.b64decode(base64_string)

        # Salvar em um ficheiro de texto
        save_filename = self.input_folder / filename

        with open(save_filename, 'wb') as file:
            file.write(decoded_bytes)

        return save_filename

    @staticmethod
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

    @staticmethod
    def update_log_table(input_folder, output_folder, file_name, new_file_name) -> bool:
        with DatabaseConnection(
            settings.DB_SERVER,
            settings.DB_DATABASE,
            settings.DB_USERNAME,
            settings.DB_PASSWORD,
        ) as db:
            current_date = datetime.now()
            current_utc_time = datetime.now(timezone.utc)

            result = db.execute_insert(
                table_name=f'{settings.DB_SCHEMA}.ZEDILOG',
                values_columns={
                    'ZTYPEDI_0': 4,
                    'NUMSEQ_0': new_file_name,
                    'PATHIN_0': input_folder,
                    'FILEIN_0': file_name,
                    'PATHOUT_0': output_folder,
                    'FILEOUT_0': new_file_name,
                    'PATHCOPY_0': input_folder,
                    'PRTFLG_0': 0,
                    'CREDAT_0': current_date.strftime('%Y-%m-%d'),
                    'CREUSR_0': 'X3WEB',
                    'CRETIM_0': current_date.strftime('%H:%M:%S'),
                    'UPDDAT_0': current_date.strftime('%Y-%m-%d'),
                    'UPDUSR_0': 'X3WEB',
                    'UPDTIM_0': current_date.strftime('%H:%M:%S'),
                    'CREDATTIM_0': current_utc_time,
                    'UPDDATTIM_0': current_utc_time,
                    'AUUID_0': uuid.uuid4(),
                },
            )

            return result['status'] == 'success'
