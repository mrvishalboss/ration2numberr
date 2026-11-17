import base64
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO

import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

try:
    import ddddocr
    _OCR_AVAILABLE = True
except Exception as _e:
    print(f"[state] ddddocr import failed: {_e!r}", file=sys.stderr, flush=True)
    _OCR_AVAILABLE = False

try:
    from PIL import Image, ImageOps
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

app = Flask(__name__)
CORS(app)

IST         = timezone(timedelta(hours=5, minutes=30))
# Vercel Free tier max timeout is 10s. Set default budget to 8s to avoid 504 Gateway errors.
TIME_BUDGET = float(os.environ.get("TIME_BUDGET", "8.0"))

API_KEY = "VKE9PnbY5k1ZYapR5PyYQ33I26sXTX569Ed7eqyg"
RAW_DATA_STRING = "e62/QaXi/grNi6mQ+lq/geomHptpmw9bHIRDgG8xX7cIonyDsUANW1RoxIEjx1SNKw1QeoIDDalROBC55PhE3sQWcfigZnmTuBNFQPkOMvRH2RVpTgNkN0pNqho0VrpE1XR8ciau99+BuUy30/EB8kf7E22CrSiqFYVpALVFnRdpObDmwsDfbzCpwN+7dHKmdDj1ZGOz6SH9mVHpgT11EgucRWuL9LT33LkHN72x6D3NvsUU8IkGKIDZxLWC53skntMAE5UbIbeISmL3u/b2chdOBG5c38NHjfRfIkDFJcfdqzL/xLQQ6zh4RzT1oUKVnRYKg0bftJ8YOqOQBrIF6A==:gM68G9IIKM73EHo5GhC5EvNDD0xeCxt5wbXDVb7qsGEjvozg33gb22kgSgqu1Q8ao7xTHEJbQvG+3ze2oR0JNZTij4chlHtPHo6T14PuO2rnDr9jDs9Psy6yQAeQ8RvbR0MRBhmLUVc8Ow7allXCEOa2XjKwrnI4ygmSowl9BY6I9RPbbQ4Uh4Fl5lT8RwUAt7jGfPlfZxeeeen66o6vrbTit+7rvE1xljE7AdqNRW1HDb3VUzKOF9m50QNfSiZPQ6IFETbMUIa+CVMXaAJwxcOcx1eDFz3tnXZvxgStxyqmE+1+WX7QrXT1afSZr9gYISf1VekHP4eoC/jBuCGz5g==:s0mG/HdrxMWUyMuhi6kxd0uWVBpPt+gGMcyRxqu9OLVJgjIF5LCcdByj04Anm/eObo1bJib8R5mrSFoxZD+wXTTaWTmA6WvTCVGbNP3SQAAjuEwdEt1KEAmqFP2gxfRnjyP56ZHGytFLkctfEQZR8WnPI5O+eheLweaLKuQ0QeWMQDQLhtYJ6a6NOguRzi315DqORzpS0CmN/oHVps0GNz5QfMreN/fn1EmNLdvS49SkDCLV8ja0/6+re+MzfSW4OJsDjh2OeEy0W5XGDRSOVzFdcazJa+3mACKWrIoh6rhpOx/tkSp1fXn7GmsJvHzdWFtLSkPe1mFDPPr3EMuMTIxIlHe6s8KpaISn7ry0whjc+XIdNpmkqXoCp9DEKd6MT6Rbq1wC6nIFKH8VqZEs4IyWyIn1P3M9dGaCiWQpNSrevmeA6FhV1gLUrbTVh3Wm8D1OwRzSWUuR8v+XKzMiIeWv7fai8Lv3qk0F+ueBd2IGPFUhkU0ly8HBqV3FRG8O"

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArpgmSqIv/3zYAxoNK/6e
LqjeBEHFsiGJCia5wdQuhCw54ceg6EyKc5mPrkEnK7CYgbJxSQO37HbnWIROMN6k
RQqxa1kZFFS+xQPZ9z4Gs+njypX8HNKcse2/kbwbIX4y8kcCENVVOV8URK8+znEs
uN/UCzJXv2Pg0KII5ofb8wAvYNXkZ44DhcWnyxO6JohbuMvpt096NBkdq8lWtRra
ppL3HqpTG4Fd5H4v9b7fD8rAhBB8cAbiM2nyBz51VDovS/SZheIemKjwGLGMDiMe
NcQGryOTZASX+jxe69NoFR9bQ8+5jN/88x5k53UzV8en+HRKbYjgUJzZOVfu3fL/
WQIDAQAB
-----END PUBLIC KEY-----"""

PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCumCZKoi//fNgD
Gg0r/p4uqN4EQcWyIYkKJrnB1C6ELDnhx6DoTIpzmY+uQScrsJiBsnFJA7fsdudY
hE4w3qRFCrFrWRkUVL7FA9n3Pgaz6ePKlfwc0pyx7b+RvBshfjLyRwIQ1VU5XxRE
rz7OcSy439QLMle/Y+DQogjmh9vzAC9g1eRnjgOFxafLE7omiFu4y+m3T3o0GR2r
yVa1GtqmkvceqlMbgV3kfi/1vt8PysCEEHxwBuIzafIHPnVUOi9L9JmF4h6YqPAY
sYwOIx41xAavI5NkBJf6PF7r02gVH1tDz7mM3/zzHmTndTNXx6f4dEptiOBQnNk5V
+7d8v9ZAgMBAAECggEActY8iWZ4L5GL+y5Nb5x/qq0DqsUgJXQNURH7qFPJbMIyKC
FH4sNFZZehe7n666+x/8zA2oeJmAz1SbFsRJSMc6T+4V6vMkIzYB6SZR71Ba1XWM6
iDsswqY95K4AQUE1TcSvnXe8TqTKygCLMKrkh80+1hs/MC2TEYDXTqN2/e+qOBq6
/RQ4A7E+Qd1R6/mFEHZJfmvMVl0lBmowHk060/JAgeSxE5VPnP2pQXad21w/nBtS
oQDOKpAzbcSIgn4vLavtUlS87XYQ8bq3Mc4sPQe9RZ9o89aQrau0SmdgNeGYVi0t
WhP2lm3b8C3XcgDQi6LwnZpzwCo9m5fEcJM4IyQKBgQD//t26TkBC2h4trvbOID2S
N2hPiBySxjb3Eoaiy58ryF/d4Im56Xf61ksuy0od52vgNzW03As6vPjTJpqy/EeJ
rOZHLdZSOiFZzqcgXUcir2O6gM/WIU/0x/Ge7nnp0DfwTYgTNzpJA+csR9aDFhOu
9e+xogJ0lV4eCEBjjC+Q+wKBgQCumOxDZkaH9uuXSbrGTsrEMO0439oLM+Er6L+P
dpy8qY0Q5ZYp2C1ZZBz8DwH6NwwKY/JcvrVVS5D90mmqsm39ubeIrmv7C04TWBQq
YRp9dgRkUkVo9BGM6EqA2q/D2JT/sr/72h5FEsMblHSVEXbCo/QLYvCglxSs7jhx
5tDIuwKBgQC/W2epJWc50cvvQDNzP3xm+Q37LXaWbJ6Xr/x+YpFX7A9lTrwFAbVT
Bq7qisGbeusTjpGR4U5vmOSzCc9n7dcX3evA102254cYl7YsJi3PiqWUu0cg/IPF
KVS/BeqR0biO45XNL2JdRBKg8g4yrOUHywVilgUZ2rGg53AiOZ8w0wKBgQCpby/A
jI0fvwiLrXo6nhX55H0hd2LTAkqe4OSdJX8fOu7xmctq2iXQHO5f0XSazDa8EpgN
VukEWCvhlgMDKtrAoiyw0ItreWIQNaaEJe2eGRxT+t7u5gPuGTLL7u0pApI9vcq/
bsF3SKjcp+mnC+aTJqZbMm3Pei4PT7KpHlQ4pwKBgDeLXCwO6cCa+4nV4t5ktCEzQ
Piu/yEMAL0hf3RwPr7WuckwyHm3cUt7DFCEf6+bJj+hpxVXGcdgVxDZjyh4s8YE8
AAd+2iv8I61gF475KAOOMbkt21TzTI0y2R2BN3JvB1iTmf6CkV6C82b4UELlKjEO
X342756ZWQbhB8Yld1T
-----END PRIVATE KEY-----"""

STATES = {
    "UTTAR PRADESH":     ("smartpds.up.gov.in", True),
    "BIHAR":             ("epos.bihar.gov.in", False),
    "JHARKHAND":         ("smartpds.jharkhand.gov.in", False),
    "HARYANA":           ("epos.haryanafood.gov.in", False),
    "ORISSA":            ("smartpds.odisha.gov.in", True),
    "DELHI":             ("epos.delhi.gov.in", False),
    "UTTARAKHAND":       ("www.epos.uk.gov.in", False),
    "WEST BENGAL":       ("smartpds.wb.gov.in", False),
    "ANDHRA PRADESH":    ("aepos.ap.gov.in", False),
    "ARUNACHAL PRADESH": ("epos.arunachal.gov.in", True),
    "TELANGANA":         ("smartpds.telangana.gov.in", False),
    "CHHATTISGARH":      ("epos.cg.gov.in", False),
    "TRIPURA":           ("epostr.gov.in", True),
    "ASSAM":             ("epos.assam.gov.in", True),
    "MEGHALAYA":         ("epos.megfcsca.gov.in", True),
    "NAGALAND":          ("epos.nagaland.gov.in", True),
    "MIZORAM":           ("epos.mizoram.gov.in", True),
    "MANIPUR":           ("www.epos.mn.gov.in", True),
    "SIKKIM":            ("epos.sikkim.gov.in", True),
    "GOA":               ("www.epos.goa.gov.in", True),
}

HIDDEN_KEYS = (
    "benficaryEntitlementHeading",
    "benficaryEntitlementList",
    "benficaryAuthenticationHeading",
    "benficaryAuthenticationsList",
    "benficaryTranscationHeading",
    "benficaryTransList",
)

_ocr = None


def crypto_decrypt(encrypted_string):
    parts = encrypted_string.strip().split(':')
    if len(parts) != 3:
        raise ValueError("Invalid encrypted shape. Expected 3 base64 segments separated by colons.")
    enc_key, enc_iv, enc_data = map(base64.b64decode, parts)
    private_key = RSA.import_key(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    cipher_aes = AES.new(cipher_rsa.decrypt(enc_key), AES.MODE_CBC, iv=cipher_rsa.decrypt(enc_iv))
    decrypted = cipher_aes.decrypt(enc_data)
    return decrypted[:-decrypted[-1]].decode('utf-8')


def crypto_encrypt(payload_dict):
    aes_key = AES.get_random_bytes(32)
    aes_iv = AES.get_random_bytes(16)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv=aes_iv)
    payload_bytes = json.dumps(payload_dict).encode('utf-8')
    padded = pad(payload_bytes, AES.block_size)
    encrypted_data = cipher_aes.encrypt(padded)
    public_key = RSA.import_key(PUBLIC_KEY_PEM)
    cipher_rsa = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    return ":".join([
        base64.b64encode(cipher_rsa.encrypt(aes_key)).decode(),
        base64.b64encode(cipher_rsa.encrypt(aes_iv)).decode(),
        base64.b64encode(encrypted_data).decode()
    ])


def fetch_umang_data(ration_card_number):
    decrypted_json_str = crypto_decrypt(RAW_DATA_STRING)
    browser_data = json.loads(decrypted_json_str)
    active_session_id = browser_data.get('sessionId')
    active_tkn = browser_data.get('tkn')
    active_usrid = browser_data.get('usrid')

    if not active_session_id or not active_tkn:
        raise Exception("Session variables not found in decrypted payload.")

    session = requests.Session()
    url = 'https://apigw.umangapp.in/onorcApi/ws1/getrationcard'

    options_headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'access-control-request-headers': 'content-type,deptid,formtrkr,srvid,subsid,subsid2,tenantid,x-api-key',
        'access-control-request-method': 'POST',
        'origin': 'https://web.umang.gov.in',
        'referer': 'https://web.umang.gov.in/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    session.options(url, headers=options_headers, timeout=10)

    new_payload = {
        "tkn": active_tkn,
        "trkr": str(random.randint(100000, 999999)),
        "lang": "en", "lat": "21", "lon": "90", "lac": "90", "usag": "90",
        "apitrkr": str(random.randint(100000, 999999)),
        "usrid": active_usrid,
        "mode": "web", "pltfrm": "linux",
        "did": str(random.randint(100000, 999999)),
        "deptid": "317", "formtrkr": "0", "srvid": "1519", "subsid": "0", "subsid2": "0",
        "id": ration_card_number,
        "sessionId": active_session_id,
        "userName": "umang", "idType": "R", "token": "Um@93259@"
    }
    encrypted_body = crypto_encrypt(new_payload)

    post_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'deptid': '317',
        'formtrkr': '0',
        'origin': 'https://web.umang.gov.in',
        'priority': 'u=1, i',
        'referer': 'https://web.umang.gov.in/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'srvid': '1519',
        'subsid': '0',
        'subsid2': '0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'x-api-key': API_KEY
    }

    res = session.post(url, headers=post_headers, data=encrypted_body, timeout=30)

    if res.status_code != 200:
        raise Exception(f"UMANG error: HTTP {res.status_code}")

    decrypted_response = crypto_decrypt(res.text)
    return json.loads(decrypted_response)


def build_headers(host: str, mobile: bool) -> dict:
    if mobile:
        ua       = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
        platform = '"Android"'
        mobile_h = "?1"
    else:
        ua       = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        platform = '"Linux"'
        mobile_h = "?0"
    origin = f"https://{host}"
    return {
        "Host":               host,
        "Connection":         "keep-alive",
        "sec-ch-ua-platform": platform,
        "User-Agent":         ua,
        "Accept":             "application/json, text/plain, */*",
        "sec-ch-ua":          '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Content-Type":       "application/json",
        "sec-ch-ua-mobile":   mobile_h,
        "Origin":             origin,
        "Sec-Fetch-Site":     "same-origin",
        "Sec-Fetch-Mode":     "cors",
        "Sec-Fetch-Dest":     "empty",
        "Referer":            f"{origin}/SRC_Trans_Int",
        "Accept-Encoding":    "gzip, deflate",
        "Accept-Language":    "en-GB,en-US;q=0.9,en;q=0.8",
    }


def _get_ocr():
    global _ocr
    if _ocr is None and _OCR_AVAILABLE:
        try:
            _ocr = ddddocr.DdddOcr(show_ad=False, beta=False)
        except Exception as e:
            print(f"[state] ddddocr model load failed: {e!r}", file=sys.stderr, flush=True)
            _ocr = None
    return _ocr


def _preprocess_for_ocr(img_bytes: bytes) -> bytes:
    if not _PIL_AVAILABLE:
        return img_bytes
    try:
        img  = Image.open(BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        if w < 150:
            scale = 150 / w
            img   = img.resize((150, int(h * scale)), Image.LANCZOS)
        gray = ImageOps.grayscale(img)
        gray = ImageOps.autocontrast(gray, cutoff=1)
        buf  = BytesIO()
        gray.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return img_bytes


def solve_captcha(img_bytes: bytes) -> str:
    if not img_bytes:
        return ""
    ocr = _get_ocr()
    if not ocr:
        return ""
    try:
        processed = _preprocess_for_ocr(img_bytes)
        text      = ocr.classification(processed)
        text      = re.sub(r"[^A-Za-z0-9]", "", text)
        if text and 4 <= len(text) <= 8:
            return text
    except Exception:
        return ""
    return ""


def _new_session(headers: dict) -> requests.Session:
    s = requests.Session()
    s.headers.update(headers)
    return s


def get_captcha(session: requests.Session, base: str, timeout: float):
    ts   = int(time.time() * 1000)
    r    = session.get(f"{base}/captcha/captcha-image?t={ts}", timeout=timeout)
    r.raise_for_status()
    data = r.json()
    image_b64 = data.get("image") or ""
    salt      = data.get("salt") or ""
    if not image_b64 or not salt:
        raise RuntimeError("Captcha response missing image/salt")
    return base64.b64decode(image_b64), salt


def query_src(session: requests.Session, base: str, month: str, year: str,
              src_no: str, captcha: str, salt: str, timeout: float):
    payload = {
        "month":   month,
        "year":    year,
        "src_no":  src_no,
        "captcha": captcha,
        "salt":    salt,
    }
    return session.post(f"{base}/sdms/SRC_Trans_Int", json=payload, timeout=timeout)


def _has_data(r: requests.Response) -> bool:
    if r.status_code != 200:
        return False
    text = r.content.decode("utf-8", errors="replace")
    return any(f'"{k}"' in text for k in HIDDEN_KEYS)


def _lookup_state(base: str, headers: dict, src_no: str, month: str, year: str):
    if not _OCR_AVAILABLE:
        print("[state] OCR not available, state lookup skipped", file=sys.stderr, flush=True)
        return None

    start         = time.time()
    last_response = None
    attempt       = 0

    while time.time() - start < TIME_BUDGET:
        attempt     += 1
        remaining    = TIME_BUDGET - (time.time() - start)
        step_timeout = max(3.0, min(10.0, remaining))
        try:
            session         = _new_session(headers)
            img_bytes, salt = get_captcha(session, base, step_timeout)
            solved          = solve_captcha(img_bytes)
            if not solved:
                print(f"[state] attempt {attempt}: captcha not solved", file=sys.stderr, flush=True)
                continue
            r             = query_src(session, base, month, year, src_no, solved, salt, step_timeout)
            last_response = r
            if _has_data(r):
                print(f"[state] attempt {attempt}: data found", file=sys.stderr, flush=True)
                return r
            print(f"[state] attempt {attempt}: no data, status {r.status_code}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[state] attempt {attempt}: error {e!r}", file=sys.stderr, flush=True)
            continue

    print(f"[state] gave up after {attempt} attempts", file=sys.stderr, flush=True)
    return last_response


def fetch_state_pds(state_name: str, ration: str):
    cfg = STATES.get(state_name.strip().upper())
    if not cfg:
        return None
    host, mobile = cfg
    base    = f"https://{host}/Epos_Spring"
    headers = build_headers(host, mobile)
    now     = datetime.now(IST)
    return _lookup_state(base, headers, ration, str(now.month), str(now.year))


def _strip_hidden(r: requests.Response):
    try:
        data = json.loads(r.content.decode("utf-8", errors="replace"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for k in HIDDEN_KEYS:
        data.pop(k, None)
    return data


@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
@app.route("/api/index", methods=["GET"])
def ration_lookup():
    ration = (request.args.get("ration") or "").strip()
    if not ration:
        return jsonify({"success": False, "error": "Ration card number is required"}), 400

    try:
        umang = fetch_umang_data(ration)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    if umang.get("rs") != "S":
        return jsonify({"success": False, "error": umang.get("rd", "UMANG lookup failed"), "umang": umang}), 502

    pd         = umang.get("pd") or {}
    state_name = (pd.get("homeStateName") or "").strip()

    state_resp = fetch_state_pds(state_name, ration) if state_name else None

    if state_resp is not None:
        data = _strip_hidden(state_resp)
        if data is not None:
            return Response(
                json.dumps(data, ensure_ascii=False, indent=2),
                status=state_resp.status_code,
                content_type="application/json; charset=utf-8",
            )
        return Response(
            state_resp.content,
            status=state_resp.status_code,
            content_type="application/json; charset=utf-8",
        )

    return Response(
        json.dumps(umang, ensure_ascii=False, indent=2),
        status=200,
        content_type="application/json; charset=utf-8",
    )

# Vercel ko ye required nahi hai, par local testing ke liye add kiya hai
if __name__ == "__main__":
    app.run(debug=True)
