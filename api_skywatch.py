# -*- coding: UTF-8 -*-

import requests
import json

def getToken(url = "https://api.farmshots.com/auth"):
    token = requests.post(url, json ={"email":"carolinapartida@verstand.solutions", "password":"farmshots"}).json()
    return token["token"]

def getPipelineList(token, per_page = 500, sort = "asc"):
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': token
    }

    body = {
        'per_page': per_page
    }

    response = requests.get('https://api.skywatch.co/earthcache/pipelines', headers=headers).json()
    return response

def createGeom(token, url = "https://image.farmshots.com/api/2/geoms"):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "bearer " + token
    }
    body = { "geometry":
        { "type": "Polygon",
        "coordinates": [ [ [ -76.72782897949217, 35.17843866156772 ],
        [ -76.66894912719725, 35.17843866156772 ],
        [ -76.66894912719725, 35.21168519745392 ],
        [ -76.72782897949217, 35.21168519745392 ],
        [ -76.72782897949217, 35.17843866156772 ]
        ] ] } }
    response = requests.post('https://image.farmshots.com/api/2/geoms', headers=headers, json=body)
    return response



def retrieveGeom(token, geom_id, url = "https://image.farmshots.com/api/2/"):
    url += "geoms/"
    url += geom_id
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "bearer " + token
    }

    response = requests.get(url, headers=headers).text
    return response

def listAssets(token, geom_id, url = "https://image.farmshots.com/api/2/"):
    url += "assets/?geom_id="
    url += geom_id
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "bearer " + token
    }
    response = requests.get(url, headers=headers).json()
    return response

def createImage(token, geom_id, asset_id, url = "https://image.farmshots.com/api/2/"):
    url += "images/"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "bearer " + token
    }
    body = {
        "asset_id": asset_id,
        "geom_id": geom_id
    }
    response = requests.post(url, headers=headers, json=body).json()
    return response

def getRGB(token, image_id, url = "https://image.farmshots.com/api/2/"):
    url += "images/"
    url += image_id + "/export?type="
    url += "tiff" + "&exprs=%"
    url += "5B%60(b4-b3)%2F(b4%2Bb3)%60%5D" + "&label="
    url += "RGB"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "bearer " + token
    }
    response = requests.get(url, headers=headers)
    print url
    return response

token = "9a9b6dd2-bdc8-41a1-8b4e-daa5eac26099"
data = getPipelineList(token)
with open('/mnt/d/Data_Analysis/skywatch/pipeline_list.json', 'w') as outfile:
    json.dump(data, outfile)
print "Archivos guardados"
