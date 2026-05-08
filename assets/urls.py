from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.AssetsDashboardView.as_view(), name='dashboard'),
    path('issue/', views.AssetIssueView.as_view(), name='issue'),
    path('<int:pk>/return/', views.AssetReturnView.as_view(), name='return'),
    path('noc/issue/', views.NOCIssueView.as_view(), name='noc_issue'),
    path('noc/<int:pk>/sign/', views.NOCSignView.as_view(), name='noc_sign'),
    path('noc/<int:pk>/template/', views.NOCTemplateDownloadView.as_view(), name='noc_template_download'),
    path('discipline/', views.DisciplineListView.as_view(), name='discipline'),
    path('discipline/<int:pk>/revoke/', views.DisciplineRevokeView.as_view(), name='discipline_revoke'),
]
