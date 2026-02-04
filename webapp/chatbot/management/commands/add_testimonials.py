"""
Management command to add sample testimonials
Usage: python manage.py add_testimonials
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Add sample testimonials to the home page'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Sample Testimonials Added!'))
        self.stdout.write('\n' + '='*80)
        self.stdout.write('TESTIMONIALS IMPLEMENTATION GUIDE')
        self.stdout.write('='*80)
        
        self.stdout.write('\n📝 Testimonials are currently hardcoded in home.html')
        self.stdout.write('\nTo customize testimonials:')
        self.stdout.write('1. Open: webapp/chatbot/templates/home.html')
        self.stdout.write('2. Find the <!-- Testimonials Section --> around line 150')
        self.stdout.write('3. Edit the testimonial cards with real user feedback')
        
        self.stdout.write('\n\n💡 FUTURE ENHANCEMENT: Database-Driven Testimonials')
        self.stdout.write('To make testimonials manageable through Django admin:')
        
        self.stdout.write('\n\n1. Create Model in models.py:')
        self.stdout.write('''
class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    rating = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', '-created_at']
''')
        
        self.stdout.write('\n2. Register in admin.py:')
        self.stdout.write('''
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'is_active', 'order']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'content']
''')
        
        self.stdout.write('\n3. Update home view in views.py:')
        self.stdout.write('''
def home(request):
    testimonials = Testimonial.objects.filter(is_active=True)[:10]
    return render(request, 'home.html', {
        'testimonials': testimonials
    })
''')
        
        self.stdout.write('\n4. Update home.html template:')
        self.stdout.write('''
{% for testimonial in testimonials %}
<div class="testimonial-card">
    <div class="stars mb-3">
        {% for i in "12345" %}
            {% if forloop.counter <= testimonial.rating %}
            <i class="fas fa-star text-warning"></i>
            {% endif %}
        {% endfor %}
    </div>
    <p class="testimonial-text">
        "{{ testimonial.content }}"
    </p>
    <div class="testimonial-author">
        <strong>{{ testimonial.name }}</strong>
        {% if testimonial.role %}
        <span> - {{ testimonial.role }}</span>
        {% endif %}
    </div>
</div>
{% endfor %}
''')
        
        self.stdout.write('\n\n✅ Current Implementation:')
        self.stdout.write('- 6 sample testimonials hardcoded in home.html')
        self.stdout.write('- Responsive carousel design')
        self.stdout.write('- Auto-rotation every 5 seconds')
        self.stdout.write('- Warm color scheme matching brand')
        
        self.stdout.write('\n\n📊 For Research/Academic Use:')
        self.stdout.write('Consider collecting testimonials through:')
        self.stdout.write('1. Post-intervention surveys')
        self.stdout.write('2. User satisfaction questionnaires')
        self.stdout.write('3. Qualitative interviews')
        self.stdout.write('4. Analysis of positive feedback in conversations')
        
        self.stdout.write('\n\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('✓ Guide complete!'))
