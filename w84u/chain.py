from w84u.models import Session
# Create your tests here.
from .Comparator import Comparator

comparator = Comparator()
last_session = comparator.get_last_session(7)

if isinstance(last_session, Session):
    # Работайте с объектом Session
    print("Last session:", last_session)
else:
    # Сообщение об ошибке
    print(last_session)