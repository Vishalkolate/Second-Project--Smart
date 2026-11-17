from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('courses/', include('courses.urls')),
    path('instructors/', include('instructors.urls')),
    path('learning/', include('learning.urls')),
    path('internships/', include('internships.urls')),
    path('attendance/', include('attendance.urls')),
    path('tasks/', include('tasks.urls')),
    path('examinations/', include('examinations.urls')),
    path('projects/', include('projects.urls')),
    path('certificates/', include('certificates.urls')),
    path('payments/', include('payments.urls')),
    path('placements/', include('placements.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
