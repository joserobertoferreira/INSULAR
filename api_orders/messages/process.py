import base64
import json

import requests

from config import settings


class ProcessMessages:
    def __init__(self, base_url, headers) -> None:
        self.service_url = f'https://{base_url}/ChangeQueuedToProcessed'
        self.headers = headers

    def update_message(self, sender, receiver, message_id) -> None:  # noqa: PLR6301
        payload = {
            'Sender': sender,
            'Receiver': receiver,
            'MessageId': message_id,
        }

        request = json.dumps(payload)

        response = requests.post(
            self.service_url, headers=self.headers, data=request
        )

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
                self.create_text_order_file(base64_string, file_name)

                # Atualizar a mensagem para processada
                self.update_message(sender, receiver, message_id)

    def create_text_order_file(self, base64_string, filename) -> None:  # noqa: PLR6301
        # Decodificando a string
        decoded_bytes = base64.b64decode(base64_string)

        # Salvando em um ficheiro de texto
        save_filename = settings.FOLDER / filename

        with open(save_filename, 'wb') as file:
            file.write(decoded_bytes)
