"""
Payroll URLs.

  /payroll/                       -> dashboard (history + incentives editor for MD)
  /payroll/generate/              -> Generate payroll for a chosen month (HR/MD)
  /payroll/approve/<id>/          -> HR/MD approve a draft
  /payroll/slip/<int:year>/<int:month>/  -> Staff downloads own slip PDF
  /payroll/tax/                   -> Tax/Stationery/Building tracking page
  /payroll/incentive/add/         -> MD-only: add incentive (HTMX-style POST)
  /payroll/incentive/delete/<id>/ -> MD-only: delete incentive
"""
from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.PayrollDashboardView.as_view(), name='dashboard'),
    path('manual-adjustments/', views.ManualAdjustmentsView.as_view(), name='manual_adjustments'),
    path('approve/<int:pk>/', views.ApproveView.as_view(), name='approve'),
    path('slip/<int:year>/<int:month>/', views.SlipView.as_view(), name='slip'),
    path('tax/', views.TaxPageView.as_view(), name='tax'),
    path('incentive/add/', views.IncentiveAddView.as_view(), name='incentive_add'),
    path('incentive/delete/<int:pk>/', views.IncentiveDeleteView.as_view(), name='incentive_delete'),
]
