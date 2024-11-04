import json

import requests


class ListQueuedMessages:
    def get_messages(base_url, receiver, headers):
        # Implementa a lógica para recuperar as mensagens
        service_url = f'https://{base_url}/ListQueuedMessageIds?Receiver={receiver}'

        response = requests.get(service_url, headers=headers)

        json_response = json.loads(response.text)

        # Reduz o número de IDs de mensagens
        # json_response['ResultData']['MessageIds'] = json_response[
        #     'ResultData'
        # ]['MessageIds'][:2]

        return {
            'CorrelationId': json_response['CorrelationId'],
            'Errors': json_response['Errors'],
            'Messages': json_response['ResultData']['MessageIds'],
        }
