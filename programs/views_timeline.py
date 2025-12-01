from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .models import Channel, Schedule


def daily_timeline(request, channel_id, date_str):
    """Render a simple RTL timeline for the channel/date.
    date_str format: YYYY-MM-DD
    """
    channel = get_object_or_404(Channel, pk=channel_id)
    qs = Schedule.objects.filter(channel=channel, schedule_date=date_str).order_by("order")
    return render(request, "programs/timeline.html", {"channel": channel, "schedules": qs, "date": date_str})


@require_POST
def timeline_reorder(request, channel_id, date_str):
    """Handle drag & drop reorder via HTMX / AJAX.
    Payload (form-data or JSON): {'updates': [{'id': schedule_id, 'order': 2, 'start': '2025-11-25T12:00:00Z'} , ...]}
    The server will validate locked items and apply cascading time updates to following items.
    """
    try:
        body = request.POST.get("updates") or request.body
        import json

        updates = json.loads(body) if isinstance(body, (bytes, str)) else body
    except Exception:
        return HttpResponseBadRequest("invalid payload")

    updated = []
    with transaction.atomic():
        # Load all schedules for day in order (for cascade)
        schedules = list(Schedule.objects.filter(channel_id=channel_id, schedule_date=date_str).order_by("order"))
        schedule_map = {s.id: s for s in schedules}

        # apply updates in incoming order
        for u in updates:
            sid = int(u.get("id"))
            if sid not in schedule_map:
                continue
            s = schedule_map[sid]
            if s.locked:
                # cannot move locked items
                continue

            new_order = int(u.get("order")) if u.get("order") is not None else s.order
            s.order = new_order
            if u.get("start"):
                dt = parse_datetime(u.get("start"))
                if dt:
                    # update instance times
                    inst = s.program_instance
                    inst.scheduled_start = dt
                    # if duration available use it
                    if inst.scheduled_end and inst.scheduled_start:
                        dur = inst.scheduled_end - inst.scheduled_start
                    else:
                        # fallback to program default duration (durationfield)
                        dur = inst.program.default_duration
                    inst.scheduled_end = inst.scheduled_start + dur
                    inst.save()
            s.save()
            updated.append(s.id)

        # Cascade: reorder schedules and avoid gaps
        ordered = Schedule.objects.filter(channel_id=channel_id, schedule_date=date_str).order_by("order", "id")
        # Ensure start times are continuous: take first start as baseline
        prev_end = None
        for s in ordered:
            inst = s.program_instance
            if prev_end is None:
                # keep existing start
                prev_end = inst.scheduled_end
            else:
                # If current start is later than prev_end, move it back to prev_end to avoid gap
                if inst.scheduled_start and inst.scheduled_start > prev_end:
                    # shift start to prev_end
                    inst.scheduled_start = prev_end
                    inst.scheduled_end = inst.scheduled_start + (inst.scheduled_end - inst.scheduled_start)
                    inst.save()
                prev_end = inst.scheduled_end

    return JsonResponse({"ok": True, "updated": updated})
