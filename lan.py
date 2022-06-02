import geocoder


def getLoaction(country, city, district):
    fullAddress = country + ','+city+','+district

    g = geocoder.arcgis(fullAddress)

    return g.latlng
