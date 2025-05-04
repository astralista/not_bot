from datetime import datetime, timedelta

def calculate_next_notification(start_date, intakes_per_day):
    """
    Рассчитывает время следующего уведомления о приеме лекарства
    
    Args:
        start_date (datetime): Дата начала приема
        intakes_per_day (int): Количество приемов в день
    
    Returns:
        list: Список времен уведомлений на сегодня
    """
    now = datetime.now()
    
    # Если количество приемов в день равно 1, уведомление в 9:00
    if intakes_per_day == 1:
        return [datetime(now.year, now.month, now.day, 9, 0)]
    
    # Если 2 приема - в 9:00 и 21:00
    if intakes_per_day == 2:
        return [
            datetime(now.year, now.month, now.day, 9, 0),
            datetime(now.year, now.month, now.day, 21, 0)
        ]
    
    # Если 3 приема - в 9:00, 15:00 и 21:00
    if intakes_per_day == 3:
        return [
            datetime(now.year, now.month, now.day, 9, 0),
            datetime(now.year, now.month, now.day, 15, 0),
            datetime(now.year, now.month, now.day, 21, 0)
        ]
    
    # Для других случаев равномерно распределяем по времени бодрствования (с 8:00 до 22:00)
    waking_hours = 14  # 14 часов бодрствования
    interval = waking_hours / intakes_per_day
    
    notification_times = []
    for i in range(intakes_per_day):
        hour = 8 + int(i * interval)
        notification_times.append(datetime(now.year, now.month, now.day, hour, 0))
    
    return notification_times

def format_medication_info(medication):
    """
    Форматирует информацию о лекарстве для отображения
    
    Args:
        medication (tuple): Данные о лекарстве из БД
    
    Returns:
        str: Отформатированная строка с информацией
    """
    med_id, user_id, name, dose, intakes, start_date, duration_val, duration_unit, break_val, break_unit, cycles = medication
    
    current_date = datetime.now().date()
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    duration_days = duration_val if duration_unit == "days" else duration_val * 30
    end_date = start_date_obj + timedelta(days=duration_days)
    days_left = (end_date - current_date).days
    
    if days_left > 0:
        status = f"⏳ Осталось: {days_left} дней"
    else:
        break_days = break_val if break_unit == "days" else break_val * 30
        next_cycle = end_date + timedelta(days=break_days)
        status = f"⏸️ Перерыв до {next_cycle.strftime('%d.%m.%Y')}"
    
    return (
        f"• <b>{name}</b> (ID: {med_id})\n"
        f"  🟢 {dose} капс. × {intakes} р/день\n"
        f"  📅 Начало: {start_date}\n"
        f"  {status}"
    )
