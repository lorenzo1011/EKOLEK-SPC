from django.contrib import admin
from .models import Question, Choice, WasteCategory, WasteItem, GameSession, UserGameCooldown, GameConfiguration

# Register your models here.

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ['text']

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question']

@admin.register(WasteCategory)
class WasteCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_hex', 'icon_name', 'created_at']
    list_filter = ['created_at']

@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'category', 'points', 'difficulty_level', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['name']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'game_type', 'game_name', 'score', 'accuracy', 'completed_at']
    list_filter = ['game_type', 'completed_at']
    search_fields = ['user__username', 'user__full_name', 'game_name']
    readonly_fields = ['completed_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


@admin.register(UserGameCooldown)
class UserGameCooldownAdmin(admin.ModelAdmin):
    list_display = ['user', 'game_type', 'last_played_at', 'can_play_status']
    list_filter = ['game_type', 'last_played_at']
    search_fields = ['user__username', 'user__full_name']
    readonly_fields = ['last_played_at', 'created_at', 'can_play_status', 'time_remaining_display']
    
    fieldsets = (
        ('User & Game', {
            'fields': ('user', 'game_type')
        }),
        ('Cooldown Status', {
            'fields': ('last_played_at', 'can_play_status', 'time_remaining_display'),
            'description': 'Current cooldown status for this user and game type'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def can_play_status(self, obj):
        can_play, time_remaining = obj.can_play_again()
        if can_play:
            return '✅ Can play'
        else:
            hours = int(time_remaining // 3600)
            minutes = int((time_remaining % 3600) // 60)
            return f'❌ Cooldown: {hours}h {minutes}m remaining'
    can_play_status.short_description = 'Status'
    
    def time_remaining_display(self, obj):
        can_play, time_remaining = obj.can_play_again()
        if can_play:
            return 'No cooldown - ready to play'
        else:
            hours = int(time_remaining // 3600)
            minutes = int((time_remaining % 3600) // 60)
            seconds = int(time_remaining % 60)
            return f'{hours} hours, {minutes} minutes, {seconds} seconds'
    time_remaining_display.short_description = 'Time Remaining'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


@admin.register(GameConfiguration)
class GameConfigurationAdmin(admin.ModelAdmin):
    list_display = ['game_type', 'cooldown_hours', 'cooldown_minutes', 'formatted_duration', 'is_active', 'updated_at']
    list_filter = ['game_type', 'is_active']
    search_fields = ['game_type']
    readonly_fields = ['created_at', 'updated_at', 'total_cooldown_display']
    
    fieldsets = (
        ('Game Information', {
            'fields': ('game_type', 'is_active')
        }),
        ('Cooldown Settings', {
            'fields': ('cooldown_hours', 'cooldown_minutes', 'total_cooldown_display'),
            'description': 'Set the cooldown duration before users can play this game again. Set cooldown to 0 or is_active to False for unrestricted play.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_duration(self, obj):
        return obj.get_formatted_duration()
    formatted_duration.short_description = 'Duration'
    
    def total_cooldown_display(self, obj):
        hours = obj.cooldown_hours
        minutes = obj.cooldown_minutes
        days = hours // 24
        remaining_hours = hours % 24
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if remaining_hours > 0:
            parts.append(f"{remaining_hours} hour{'s' if remaining_hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        return " ".join(parts) if parts else "0 minutes (unrestricted play)"
    total_cooldown_display.short_description = 'Total Duration'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
