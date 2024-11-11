from abilityhub.models import Person

def person_context(request):
    if request.user.is_authenticated:
        try:
            person = Person.objects.get(user=request.user)
            return {'auth_person': person}
        except Person.DoesNotExist as e:
            print(f'--- CONTEXT PROCESSOR EXCEPTION ---: {e}')
            return {}
    return {}