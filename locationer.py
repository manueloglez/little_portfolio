from urllib2 import urlopen
import xmltodict
import json
def getplace(lat, lon, internacional):
    url = "http://dev.virtualearth.net/REST/v1/Locations/"
    url += "%s,%s" % (lat, lon)
    url += "?o=xml&key=AnrplNy9O1LFauGfaRpz42hvw4aDqyqV-ybsE-x-rcet-YNHPl_VKpIrkJ3sxu6M"
    v = urlopen(url).read()
    xpars = xmltodict.parse(v)
    j = json.dumps(xpars)
    components = xpars["Response"]["ResourceSets"]["ResourceSet"]["Resources"]["Location"]["Address"]
    country = town = None
    noCiudad = False
    pais = ciudad = estado = "DESCONOCIDO"
    for c in components.keys():
        if c == "AdminDistrict":
            estado = components[c]
        elif c == "AdminDistrict2":
            ciudad = components[c]
        else:
            pass
        if c == "CountryRegion":
            pais = components[c]
    if pais == "Mexico":
        return ciudad, estado
    else:
        return ciudad, pais
