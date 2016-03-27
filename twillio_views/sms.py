from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from parsers.html_parsers import strip_tags
import time

GOOGLE_API_KEY = 'AIzaSyCOSaYoVFlZK67ox5gDTMLtHFsm221gEAE'
KEYWORDS = ['mode', 'to', 'from']

#need to fix this too so don't need csrf expemtion
@csrf_exempt
def sms_request(request):
    text = request.POST.get('Body', '').lower()
    if is_valid_request(text):
        optional_mode_query = ''
        if 'mode' in text:
            requested_mode = get_keyword_arg(text, 'mode')
            if not valid_mode(requested_mode):
                return HttpResponse('<Response><Message>Invalid mode requested. Please send request again using driving, walking, or bicycling as the mode. Unfortunately transit is not yet available.</Message></Response>', content_type='text/xml')
            optional_mode_query = '&mode=' + requested_mode
        #need to handle situation in which no from next.
        from_address_query = get_keyword_arg(text, 'from').replace(' ','+')
        to_address_query = get_keyword_arg(text, 'to').replace(' ','+')
        #also handle google api errors here.
        google_maps_response = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin=' + from_address_query + '&destination=' + to_address_query + optional_mode_query + '&key=' + GOOGLE_API_KEY)
        if google_maps_response.status_code == requests.codes.ok:
            google_maps_json = google_maps_response.json()
            if google_maps_json['geocoded_waypoints'][0]['geocoder_status'] != "OK":
                return HttpResponse('<Response><Message>Unable to recognize your origin. Please revise the address and try again.</Message></Response>', content_type='text/xml')
            if google_maps_json['geocoded_waypoints'][1]['geocoder_status'] != "OK":
                return HttpResponse('<Response><Message>Unable to recognize your destination. Please revise the address and try again.</Message></Response>', content_type='text/xml')
            origin = google_maps_json['routes'][0]['legs'][0]['start_address']
            destination = google_maps_json['routes'][0]['legs'][0]['end_address']
            twiml_response = '<Response><Message> Directions from ' + origin + ' to ' + destination + ' provided courtesy of Google Maps and the smsRouting project.</Message>'
            steps = google_maps_json['routes'][0]['legs'][0]['steps']
            #consider making into 1 message for $$ saving.
            for i in range(0,len(steps)):
                instructions = strip_tags(steps[i]['html_instructions'])
                distance = steps[i]['distance']['text']
                duration = steps[i]['duration']['text']
                twiml_response = twiml_response + '<Message>' + str(i+1) +'. ' + instructions + ' for '+ distance + ', ' + duration + '.' + '</Message>'
                # becauase twillio's API is too slow and mis-orders the text responses sometimes.
                time.sleep(.01)
            twiml_response = twiml_response + '</Response>'
            return HttpResponse(twiml_response, content_type='text/xml')
        else:
            #handle specific error codes later
            return HttpResponse('<Response><Message>Something has gone wrong with your request. Please try again.</Message></Response>', content_type='text/xml')
    else:
        return HttpResponse('<Response><Message> Please send valid message. All messages must be of the format from (origin address) to (destination address). Optionally you may inlude mode (type of directions) too.</Message></Response>', content_type='text/xml')

def get_keyword_arg(text, keyword):
    text = text.split(keyword)[1]
    for other_keyword in KEYWORDS:
        text = text.split(other_keyword)[0]
    return text.strip()

def valid_mode(text):
    return (text == 'driving') or (text == 'walking') or (text == 'bicycling')

def is_valid_request(text):
    return ('to' in text) and ('from' in text)



