from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    # Mail boxes
    path('inbox/',                              views.inbox,                    name='inbox'),
    path('sent/',                               views.sent_mails,               name='sent_mails'),
    path('compose/',                            views.compose,                  name='compose'),
    path('mail/<int:mail_id>/',                 views.mail_detail,              name='mail_detail'),

    # Customised mails hub
    path('customized/',                         views.send_promotion,           name='send_promotion'),

    # Offer letter flow (HR)
    path('offer-letter/',                       views.generate_offer_letter,    name='generate_offer_letter'),
    path('offer-letter/<int:offer_id>/preview/',views.offer_preview,            name='offer_preview'),
    path('offer-letter/<int:offer_id>/edit/',   views.offer_edit,               name='offer_edit'),

    # Candidate-facing accept page (public, no login)
    path('accept/<uuid:token>/',               views.offer_accept,             name='offer_accept'),

    # HR verifies acceptance mail → activates employee
    path('mail/<int:mail_id>/verify/',          views.verify_acceptance,        name='verify_acceptance'),

    # Promotion letter
    path('promotion-letter/',                   views.generate_promotion_letter,name='generate_promotion_letter'),
]
