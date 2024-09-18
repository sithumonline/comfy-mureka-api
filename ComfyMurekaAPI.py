import requests
import json
import logging


logging.basicConfig(level=logging.INFO)


class MurekaGenerate:
    def __init__(self):
        self.base_url = "https://static-cos.mureka.ai/"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cookie": ("STRING", {"multiline": True}),
                "title": ("STRING", {"multiline": False}),
                "prompt": ("STRING", {"multiline": True}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "DICT")
    RETURN_NAMES = ("audio_url1", "audio_url2", "response")
    FUNCTION = "run"

    CATEGORY = "Mureka"

    def generate(self, cookie, title, lyrics):
        url = 'https://www.mureka.ai/api/pgc/feed/generate'
        headers = {
            'content-type': 'application/json',
            'cookie': cookie
        }
        payload = {
            "title": title,
            "lyrics": lyrics
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        return response_json['data']['conn_id']


    def subscribe(self, cookie, conn_id):
        url = f'https://www.mureka.ai/api/sse/subscribe?conn_id={conn_id}'
        headers = {
            'accept': 'text/event-stream',
            'cookie': cookie,
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response.text


    def process_event_stream(self, event_stream):
        try:
            for line in event_stream.split('\n'):
                if line.startswith('data:'):
                    data = json.loads(line[5:])
                    if data['state'] == 3:
                        return data

        except json.JSONDecodeError as e:
            logging.error(f"[Mureka] JSON decode error: {e}")
        except Exception as e:
            logging.error(f"[Mureka] Unexpected error: {e}")

        return None


    def construct_audio_url(self, audio_path):
        return f"{self.base_url}{audio_path}"    


    def run(self, cookie, title, prompt):
        try:
            conn_id = self.generate(cookie, title, prompt)

            logging.info(f"[Mureka] conn_id: {conn_id}")

            event_stream = self.subscribe(cookie, conn_id)
            if event_stream is None:
                logging.error("[Mureka] Event stream is None")
                return None, None, None

            logging.info(f"[Mureka] Event stream received \n\n{event_stream}")

            response = self.process_event_stream(event_stream)
            if response is None:
                logging.error("[Mureka] Response is None")
                return None, None, None
            
            audio_url1 = self.construct_audio_url(response['songs'][0]['mp3_url'])
            audio_url2 = self.construct_audio_url(response['songs'][1]['mp3_url'])

            return audio_url1, audio_url2, response

        except Exception as e:
            logging.error(f"[Mureka] Unexpected error in run method: {e}")
            return None, None, None
