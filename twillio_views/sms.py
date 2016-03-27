from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from parsers.html_parsers import strip_tags
import time

GOOGLE_API_KEY = 'AIzaSyCOSaYoVFlZK67ox5gDTMLtHFsm221gEAE'
KEYWORDS = ['mode', 'to', 'from']

@csrf_exempt
def sms_request(request):
    text = request.POST.get('Body', '').lower()
    if is_valid_request(text):
        optional_mode_query = ''
        if 'mode' in text:
            requested_mode = get_keyword_arg(text, 'mode')
            if not valid_mode(requested_mode):
                return HttpResponse('<Response><Message>Invalid mode requested. Please send request again using driving, walking, bicycling, or tansit as the mode.</Message></Response>', content_type='text/xml')
            optional_mode_query = '&mode=' + requested_mode
        #need to handle situation in which no from next.
        from_address_query = get_keyword_arg(text, 'from').replace(' ','+')
        to_address_query = get_keyword_arg(text, 'to').replace(' ','+')
        #also handle google api errors here.
        google_maps_response = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin=' + from_address + '&destination=' + to_address+ optional_mode_query + '&key=' + GOOGLE_API_KEY)
        twiml_response = '<Response>'
        steps = google_maps_response.json()['routes'][0]['legs'][0]['steps']
        for i in range(0,len(steps)):
            twiml_response = twiml_response + '<Message>' + str(i+1) +'. ' + strip_tags(steps[i]['html_instructions']) + '</Message>'
            time.sleep(.01)
        twiml_response = twiml_response + '</Response>'
        return HttpResponse(twiml_response, content_type='text/xml')
    else:
        return HttpResponse('<Response><Message> Please send valid message</Message></Response>', content_type='text/xml')

def get_keyword_arg(text, keyword):
    text = text.split(keyword)[1]
    for other_keyword in KEYWORDS:
        text = text.split(other_keyword)[0]
    return text.strip()

def valid_mode(text):
    return (text == 'driving') or (text == 'walking') or (text == 'bicycling') or (text=='transit')

def is_valid_request(text):
    return ('to' in text) and ('from' in text)
