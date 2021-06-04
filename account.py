import requests
import json

url = "https://ise:8910/pxgrid/control/AccountCreate"

payload = json.dumps({
  "nodeName": "AdamApp1"
})
headers = {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

print(response.text)
