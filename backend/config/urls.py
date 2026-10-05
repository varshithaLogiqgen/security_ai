"""Versioned API organized in the same feature order as the React workspace."""
from django.urls import path
from django.http import JsonResponse
from apps.identity import views as identity
from apps.dashboard import views as dashboard
from apps.projects import views as projects
from apps.work_updates import views as updates
from apps.people import views as people
from apps.documents import views as documents
from apps.assistant import views as assistant
from apps.search import views as search
from apps.notifications import views as notifications
from apps.administration import views as administration
from apps.audit import views as audit

def health(request): return JsonResponse({'status':'ok'})

routes=[
    ('auth/accept', identity.accept_invitation),
    ('health',health),('me',identity.me),('auth/login',identity.sign_in),('auth/logout',identity.sign_out),('auth/callback',identity.callback),('auth/csrf',identity.csrf),
    ('dashboard',dashboard.overview),
    ('projects',projects.projects),('projects/<str:pk>',projects.project),('projects/<str:pk>/documents',documents.project_documents),('teams',projects.teams),
    ('updates',updates.updates),('updates/<str:pk>',updates.update),('updates/<str:pk>/publish',updates.publish),('updates/<str:pk>/request-deletion',updates.request_deletion),('teams/<str:pk>/updates',updates.team_updates),
    ('profiles',people.directory),('profiles/<str:pk>',people.profile),('profiles/<str:pk>/personal',people.personal),
    ('documents',documents.documents),('documents/<str:pk>',documents.document),('documents/<str:pk>/publish',documents.publish),('documents/<str:pk>/access',documents.access),('documents/<str:pk>/versions',documents.versions),('documents/<str:pk>/download',documents.download),('documents/<str:pk>/request-deletion',documents.request_deletion),
    ('conversations',assistant.conversations),('conversations/<str:pk>',assistant.conversation),('conversations/<str:pk>/messages',assistant.messages),('citations/<str:pk>',assistant.citation),
    ('search',search.search),('notifications',notifications.notifications),('notifications/<str:pk>/read',notifications.mark_read),
    ('admin/users',administration.users),('admin/invitations',administration.invitations),('admin/users/<str:pk>/deactivate',administration.deactivate),('admin/teams',administration.teams),('admin/projects',administration.projects),('admin/access-requests',administration.access_requests),('admin/approvals',administration.approvals),('admin/approvals/<str:pk>/review',administration.approval_review),
    ('security/audit',audit.events),
]
urlpatterns=[path(f'api/v1/{route}',view) for route,view in routes]
handler404=lambda request,exception=None:JsonResponse({'detail':'This page is unavailable or you no longer have access.'},status=404)
handler500=lambda request:JsonResponse({'detail':'This service is temporarily unavailable.'},status=500)
