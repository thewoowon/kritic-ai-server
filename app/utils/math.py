import math

# 하버사인 공식

def haversine(lat1, lon1, lat2, lon2):
    # 두 지점의 위도 경도를 라디안으로 변환
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # 지구의 반지름(k m)
    return c * r


# Vincenty 공식

def vincenty(lat1, lon1, lat2, lon2):
    a = 6378137
    b = 6356752.314245
    f = 1 / 298.257223563
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    sinU1 = math.sin(U1)
    cosU1 = math.cos(U1)
    sinU2 = math.sin(U2)
    cosU2 = math.cos(U2)
    cosSqAlpha = 0
    sinSigma = 0
    cos2SigmaM = 0
    cosSigma = 0
    sigma = 0
    sinLambda = 0
    cosLambda = 0
    sinAlpha = 0
    C = 0
    Lambda = L
    for i in range(1000):
        sinLambda = math.sin(Lambda)
        cosLambda = math.cos(Lambda)
        sinSigma = math.sqrt(
            (cosU2 * sinLambda) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha ** 2
        cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        LambdaP = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma *
                                               (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM ** 2)))
        if abs(Lambda - LambdaP) <= 1e-12:
            break
    uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma * (-1 + 2 * cos2SigmaM ** 2) -
                                 B / 6 * cos2SigmaM * (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    s = b * A * (sigma - deltaSigma)
    return s
# Compare this snippet from app/utils/math.py:
