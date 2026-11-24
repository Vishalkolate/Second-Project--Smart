from accounts.models import SystemSetting
from notifications.models import Notification


def global_context(request):
    setting = SystemSetting.objects.first()
    if not setting:
        setting = SystemSetting.objects.create(
            institute_name="Smart LMS & Internship Management System",
            tagline="Practical Learning & Industry Internship Platform",
            email="a2zithub@smartlms.edu",
            phone="+91 98765 43210",
            address="A2Z IT HUB Balikashram Rd, Bagade Mala, Ahilyanagar, Maharashtra 414003"
        )
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return {
        'site_setting': setting,
        'unread_notifications_count': unread_count,
    }
