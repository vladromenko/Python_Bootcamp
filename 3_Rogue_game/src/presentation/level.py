import curses
import math

from consts import MAP_WIDTH, MAP_HEIGHT, VIEW_3D_FOV, VIEW_3D_DISTANCE, RAY_STEP, MINIMAP_WIDTH, MINIMAP_HEIGHT, \
    MINIMAP_OFFSET_X, MINIMAP_OFFSET_Y, VIEW_3D_OFFSET_Y, VISIBILITY_DISTANCE
from domain.utils import Position, get_bresenham_line_coords, DoorColor
from presentation.objects import get_object_sym, get_object_color
from domain.items import ItemObjects


def display_map(stdscr, level, player, is_3d_mode=False, view_angle=0.0):
    if is_3d_mode:
        display_3d_view(stdscr, level, player, view_angle)
        return
    create_new_map(level, player)

    shift_x = 6
    shift_y = 2

    for i in range(MAP_HEIGHT):
        stdscr.move(shift_y + i, shift_x)

        for j in range(MAP_WIDTH):
            stdscr.addch(level.map[i][j], get_object_color(level.map[i][j]))

    stdscr.move(shift_y + MAP_HEIGHT, shift_x)
    stdscr.addstr(f"Level: {level.level_num:<5}")
    stdscr.addstr(f"Gold: {sum(treasure.price for treasure in player.backpack.treasures):<5}")
    stdscr.addstr(f"Health: {player.health}/{player.max_health:<6}")
    stdscr.addstr(f"Agility: {player.agility:<5}")
    stdscr.addstr(f"Strength: {player.strength:}")
    if player.weapon:
        stdscr.addstr(f"(+{player.weapon.increase})")
    stdscr.addstr(" Mode: 2D (T)")
    stdscr.refresh()


def create_new_map(level, player):
    level.map = [[' ' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    rooms_to_map(level)
    exit_to_map(level)
    corridors_to_map(level)
    items_to_map(level)
    monsters_to_map(level)
    ray_cast_to_map(level, player)
    player_to_map(level, player)


def rooms_to_map(level):
    for room in level.rooms:
        if not room.was_visited:
            continue

        x_start = room.coords.x
        y_start = room.coords.y
        x_end = x_start + room.width
        y_end = y_start + room.height

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                check_x = (x == x_start or x == x_end - 1) and (y_start <= y <= y_end)
                check_y = (y == y_start or y == y_end - 1) and (x_start <= x <= x_end)
                if check_y:
                    level.map[y][x] = curses.ACS_HLINE
                elif check_x:
                    level.map[y][x] = curses.ACS_VLINE
                elif room.visible:
                    level.map[y][x] = '.'
        level.map[y_start][x_start] = curses.ACS_ULCORNER
        level.map[y_start][x_end - 1] = curses.ACS_URCORNER
        level.map[y_end - 1][x_start] = curses.ACS_LLCORNER
        level.map[y_end - 1][x_end - 1] = curses.ACS_LRCORNER


def player_to_map(level, player):
    x = player.coords.x
    y = player.coords.y
    level.map[y][x] = get_object_sym(player)


def exit_to_map(level):
    x = level.end_of_level.x
    y = level.end_of_level.y

    room = level.get_room_by_coord(level.end_of_level)
    if room.visible:
        level.map[y][x] = 'E'


def monsters_to_map(level):
    for monster in level.monsters:
        place = level.get_place_by_coord(monster.coords)
        door = level.is_door_coord(monster.coords)
        door_room = level.get_room_for_doors_by_coord(monster.coords)
        corridor = level.get_corridor_by_coord(monster.coords)
        if door and not door_room.visible and not corridor.visible:
            continue
        elif not door and not place.visible:
            continue
        x = monster.coords.x
        y = monster.coords.y
        level.map[y][x] = get_object_sym(monster)


def corridors_to_map(level):
    for corridor in level.corridors:
        x_start = corridor.coords.x
        y_start = corridor.coords.y
        x_end = x_start + corridor.width
        y_end = y_start + corridor.height

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                check_x = (x_start < x < x_end - 1) and (y_start < y < y_end - 1)
                if not check_x:
                    continue

                # Проверяем, есть ли здесь дверь
                door_found = False
                for door_coords, door_color in corridor.doors:
                    if door_coords.x == x and door_coords.y == y:
                        door_found = True

                        # ПРОВЕРЯЕМ, ОБНАРУЖЕНА ЛИ ДВЕРЬ
                        room = level.get_room_for_doors_by_coord(Position(x=x, y=y))
                        corridor_discovered = corridor.was_visited or corridor.visible
                        room_discovered = room and (room.was_visited or room.visible)

                        # Дверь показываем только если:
                        # 1. Игрок уже был в комнате или коридоре с этой дверью
                        # 2. ИЛИ дверь уже была обнаружена ранее
                        if (corridor_discovered or room_discovered or
                                corridor.is_door_discovered(Position(x, y)) or
                                (room and room.is_door_discovered(Position(x, y)))):

                            if door_color == DoorColor.NONE:
                                level.map[y][x] = '/'  # Обычная дверь
                            elif door_color == DoorColor.RED:
                                level.map[y][x] = 'R'  # Красная дверь
                            elif door_color == DoorColor.GREEN:
                                level.map[y][x] = 'G'  # Зеленая дверь
                            elif door_color == DoorColor.BLUE:
                                level.map[y][x] = 'B'  # Синяя дверь
                            elif door_color == DoorColor.YELLOW:
                                level.map[y][x] = 'Y'  # Желтая дверь
                        else:
                            # Дверь не обнаружена - показываем стену коридора
                            if corridor.was_visited:
                                level.map[y][x] = '#'
                            else:
                                level.map[y][x] = ' '

                        break

                if door_found:
                    continue

                room = level.get_room_for_doors_by_coord(Position(x=x, y=y))
                if room and room.was_visited or room and corridor.visible:
                    level.map[y][x] = '+'
                elif corridor.was_visited:
                    level.map[y][x] = '#'


def items_to_map(level):
    places = level.rooms + level.corridors
    for place in places:
        if not place.visible:
            continue
        for item in place.items:
            x = item.coords.x
            y = item.coords.y
            level.map[y][x] = get_object_sym(item)

            # Если это ключ, установим правильный цвет
            if hasattr(item, 'type') and item.type == ItemObjects.KEY:
                # Установим символ ключа
                level.map[y][x] = 'k'


def display_3d_view(stdscr, level, player, view_angle):
    info_line = _capture_info_line(stdscr)
    stdscr.erase()
    ctx = _build_3d_context(stdscr, player)
    if not ctx:
        return
    _render_3d_columns(stdscr, level, view_angle, ctx)
    sprites = _collect_visible_sprites(level, player)
    _render_sprites(stdscr, sprites, ctx, view_angle)
    create_new_map(level, player)
    _draw_minimap(stdscr, level, player, ctx["max_x"], ctx["max_y"])
    _draw_status_line(stdscr, level, player, ctx["max_y"])
    _restore_info_line(stdscr, info_line)
    stdscr.refresh()


def _build_3d_context(stdscr, player):
    max_y, max_x = stdscr.getmaxyx()
    view_height = max_y - VIEW_3D_OFFSET_Y - 1
    view_width = max_x
    if view_height <= 0 or view_width <= 0:
        return None
    start_x = player.coords.x + 0.5
    start_y = player.coords.y + 0.5
    ctx = {
        "max_y": max_y,
        "max_x": max_x,
        "view_height": view_height,
        "view_width": view_width,
        "half_fov": VIEW_3D_FOV / 2,
        "view_bottom": VIEW_3D_OFFSET_Y + view_height - 1,
        "start_x": start_x,
        "start_y": start_y,
        "depth_buffer": [VIEW_3D_DISTANCE for _ in range(view_width)],
        "ceiling_chars": [' ', '.', '`'],
        "floor_chars": ['.', ',', ';', ':'],
    }
    return ctx


def _render_3d_columns(stdscr, level, view_angle, ctx):
    for screen_x in range(ctx["view_width"]):
        _render_3d_column(stdscr, level, view_angle, ctx, screen_x)


def _render_3d_column(stdscr, level, view_angle, ctx, screen_x):
    ray_angle = _calc_ray_angle(screen_x, ctx["view_width"], view_angle, ctx["half_fov"])
    ray_cos = math.cos(ray_angle)
    ray_sin = math.sin(ray_angle)
    distance, hit_x, hit_y, tunnel_hit = _cast_ray(level, ctx["start_x"], ctx["start_y"], ray_cos, ray_sin)
    perp_distance = _perp_distance(distance, ray_angle, view_angle)
    ctx["depth_buffer"][screen_x] = perp_distance
    wall_top, wall_bottom = _wall_bounds(ctx["view_height"], perp_distance)
    wall_char = _select_wall_char(perp_distance, hit_x, hit_y, tunnel_hit)
    _draw_wall_column(stdscr, screen_x, ctx, wall_top, wall_bottom, wall_char)


def _calc_ray_angle(screen_x, view_width, view_angle, half_fov):
    return view_angle - half_fov + (screen_x / max(1, view_width)) * VIEW_3D_FOV


def _cast_ray(level, start_x, start_y, ray_cos, ray_sin):
    distance = 0.0
    hit_x = start_x
    hit_y = start_y
    tunnel_hit = False
    hit_wall = False
    while distance < VIEW_3D_DISTANCE and not hit_wall:
        distance += RAY_STEP
        test_x = int(start_x + ray_cos * distance)
        test_y = int(start_y + ray_sin * distance)
        hit_wall = _is_wall(level, test_x, test_y)
        if hit_wall:
            tunnel_hit = _is_tunnel_mark(level, test_x, test_y)
            hit_x = start_x + ray_cos * distance
            hit_y = start_y + ray_sin * distance
    return distance, hit_x, hit_y, tunnel_hit


def _perp_distance(distance, ray_angle, view_angle):
    return max(distance * math.cos(ray_angle - view_angle), 0.01)


def _wall_bounds(view_height, perp_distance):
    wall_height = int(view_height / perp_distance)
    wall_top = VIEW_3D_OFFSET_Y + max((view_height - wall_height) // 2, 0)
    wall_bottom = min(wall_top + wall_height, VIEW_3D_OFFSET_Y + view_height - 1)
    return wall_top, wall_bottom


def _draw_wall_column(stdscr, screen_x, ctx, wall_top, wall_bottom, wall_char):
    for screen_y in range(VIEW_3D_OFFSET_Y, VIEW_3D_OFFSET_Y + ctx["view_height"]):
        if screen_y < wall_top:
            stdscr.addch(screen_y, screen_x, _ceiling_char(screen_y, wall_top, ctx))
        elif screen_y <= wall_bottom:
            stdscr.addch(screen_y, screen_x, wall_char)
        else:
            stdscr.addch(screen_y, screen_x, _floor_char(screen_y, wall_bottom, ctx))


def _ceiling_char(screen_y, wall_top, ctx):
    denom = max(1, wall_top - VIEW_3D_OFFSET_Y)
    ratio = (wall_top - screen_y) / denom
    index = min(len(ctx["ceiling_chars"]) - 1, int(ratio * len(ctx["ceiling_chars"])))
    return ctx["ceiling_chars"][index]


def _floor_char(screen_y, wall_bottom, ctx):
    denom = max(1, ctx["view_bottom"] - wall_bottom)
    ratio = (screen_y - wall_bottom) / denom
    index = min(len(ctx["floor_chars"]) - 1, int(ratio * len(ctx["floor_chars"])))
    return ctx["floor_chars"][index]


def _draw_status_line(stdscr, level, player, max_y):
    status_y = max_y - 1
    stdscr.move(status_y, 1)
    stdscr.clrtoeol()
    stdscr.addstr(f"Level: {level.level_num:<5}")
    stdscr.addstr(f"Gold: {sum(treasure.price for treasure in player.backpack.treasures):<5}")
    stdscr.addstr(f"Health: {player.health}/{player.max_health:<6}")
    stdscr.addstr(f"Agility: {player.agility:<5}")
    stdscr.addstr(f"Strength: {player.strength:}")
    if player.weapon:
        stdscr.addstr(f"(+{player.weapon.increase})")
    stdscr.addstr(" Mode: 3D (T)")


def _capture_info_line(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    if max_y <= 0 or max_x <= 1:
        return ""
    raw_line = stdscr.instr(0, 1, max_x - 1)
    return raw_line.decode("utf-8", errors="ignore").rstrip("\x00")


def _restore_info_line(stdscr, info_line):
    if not info_line:
        return
    max_y, max_x = stdscr.getmaxyx()
    if max_y <= 0 or max_x <= 1:
        return
    stdscr.move(0, 1)
    stdscr.clrtoeol()
    stdscr.addstr(0, 1, info_line[: max_x - 2])


def _draw_minimap(stdscr, level, player, max_x, max_y):
    half_w = MINIMAP_WIDTH // 2
    half_h = MINIMAP_HEIGHT // 2
    map_start_x = max(0, min(player.coords.x - half_w, MAP_WIDTH - MINIMAP_WIDTH))
    map_start_y = max(0, min(player.coords.y - half_h, MAP_HEIGHT - MINIMAP_HEIGHT))
    for dy in range(MINIMAP_HEIGHT):
        map_y = map_start_y + dy
        screen_y = MINIMAP_OFFSET_Y + dy
        if 0 <= screen_y < max_y:
            for dx in range(MINIMAP_WIDTH):
                map_x = map_start_x + dx
                screen_x = MINIMAP_OFFSET_X + dx
                if 0 <= screen_x < max_x:
                    if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                        cell = level.map[map_y][map_x]
                    else:
                        cell = ' '
                    stdscr.addch(screen_y, screen_x, cell, get_object_color(cell))
    player_x = MINIMAP_OFFSET_X + (player.coords.x - map_start_x)
    player_y = MINIMAP_OFFSET_Y + (player.coords.y - map_start_y)
    if 0 <= player_x < max_x and 0 <= player_y < max_y:
        stdscr.addch(player_y, player_x, '@', get_object_color('@'))
    return map_start_x, map_start_y


def _is_wall(level, x, y):
    if x < 0 or y < 0 or x >= MAP_WIDTH or y >= MAP_HEIGHT:
        return True
    place = level.get_place_by_coord(Position(x=x, y=y))
    if not place:
        return True
    if not place.visible:
        return True
    return False


def _is_tunnel_mark(level, x, y):
    if x < 0 or y < 0 or x >= MAP_WIDTH or y >= MAP_HEIGHT:
        return False
    corridor = level.get_corridor_by_coord(Position(x=x, y=y))
    if not corridor:
        return False
    if corridor.visible:
        return False
    room = level.get_room_for_doors_by_coord(Position(x=x, y=y))
    if not room or not room.was_visited:
        return False
    return True


def _select_wall_char(distance, hit_x, hit_y, is_tunnel):
    if is_tunnel:
        return '|'
    patterns = [('#', '@'), ('O', '0'), ('X', 'x'), ('+', '-')]
    band_size = VIEW_3D_DISTANCE / len(patterns)
    band = int(distance / band_size)
    if band >= len(patterns):
        band = len(patterns) - 1
    pair = patterns[band]
    selector = (int(hit_x * 2) + int(hit_y * 2)) % 2
    return pair[selector]


def _normalize_angle(angle):
    while angle <= -math.pi:
        angle += 2 * math.pi
    while angle > math.pi:
        angle -= 2 * math.pi
    return angle


def _collect_visible_sprites(level, player):
    sprites = []
    for monster in level.monsters:
        place = level.get_place_by_coord(monster.coords)
        if place and place.visible:
            sym = get_object_sym(monster)
            if sym and sym != '.':
                sprites.append((monster.coords.x + 0.5, monster.coords.y + 0.5, sym))
    for place in level.rooms + level.corridors:
        if place.visible:
            for item in place.items:
                sym = get_object_sym(item)
                if sym:
                    sprites.append((item.coords.x + 0.5, item.coords.y + 0.5, sym))
    exit_room = level.get_room_by_coord(level.end_of_level)
    if exit_room and exit_room.visible:
        sprites.append((level.end_of_level.x + 0.5, level.end_of_level.y + 0.5, 'E'))
    return sprites


def _render_sprites(stdscr, sprites, ctx, view_angle):
    if not sprites:
        return
    prepared = _prepare_sprite_data(sprites, ctx["start_x"], ctx["start_y"])
    for sprite_data in prepared:
        _render_sprite(stdscr, sprite_data, ctx, view_angle)


def _prepare_sprite_data(sprites, start_x, start_y):
    prepared = []
    for sprite_x, sprite_y, sprite_char in sprites:
        dx = sprite_x - start_x
        dy = sprite_y - start_y
        distance = math.hypot(dx, dy)
        if distance > 0.01:
            prepared.append((distance, sprite_char, dx, dy))
    prepared.sort(key=lambda x: x[0], reverse=True)
    return prepared


def _render_sprite(stdscr, sprite_data, ctx, view_angle):
    distance, sprite_char, dx, dy = sprite_data
    projection = _sprite_projection(distance, dx, dy, view_angle, ctx)
    if not projection:
        return
    left, right, top, bottom, perp_distance = projection
    _draw_sprite_columns(stdscr, sprite_char, left, right, top, bottom, perp_distance, ctx["view_width"],
                         ctx["depth_buffer"])


def _sprite_projection(distance, dx, dy, view_angle, ctx):
    angle = math.atan2(dy, dx)
    angle_diff = _normalize_angle(angle - view_angle)
    if abs(angle_diff) > ctx["half_fov"]:
        return None
    perp_distance = max(distance * math.cos(angle_diff), 0.01)
    sprite_height = min(int(ctx["view_height"] / perp_distance), ctx["view_height"])
    sprite_width = max(1, sprite_height // 2)
    center_x = int((angle_diff + ctx["half_fov"]) / VIEW_3D_FOV * ctx["view_width"])
    left = center_x - sprite_width // 2
    right = center_x + sprite_width // 2
    top = VIEW_3D_OFFSET_Y + max((ctx["view_height"] - sprite_height) // 2, 0)
    bottom = min(top + sprite_height, ctx["view_bottom"])
    return left, right, top, bottom, perp_distance


def _draw_sprite_columns(stdscr, sprite_char, left, right, top, bottom, perp_distance, view_width, depth_buffer):
    for screen_x in range(left, right + 1):
        if 0 <= screen_x < view_width and perp_distance < depth_buffer[screen_x]:
            for screen_y in range(top, bottom + 1):
                stdscr.addch(screen_y, screen_x, sprite_char, get_object_color(sprite_char))


def ray_cast_to_map(level, player):
    next_room = level.get_next_room(player)
    if not next_room:
        return

    visible_coords = cast_ray(level, next_room, player, VISIBILITY_DISTANCE)

    # ОБНАРУЖЕНИЕ ДВЕРЕЙ В ЗОНЕ ВИДИМОСТИ
    for coords in visible_coords:
        x, y = coords
        # Проверяем, есть ли здесь дверь
        if level.is_door_coord(Position(x, y)):
            # Обнаруживаем дверь
            place = level.get_place_by_coord(Position(x, y))
            if place:
                place.discover_door(Position(x, y))

            # Также отмечаем в комнате
            room = level.get_room_for_doors_by_coord(Position(x, y))
            if room:
                room.discover_door(Position(x, y))

    x_start = next_room.coords.x + 1
    y_start = next_room.coords.y + 1
    x_end = x_start + next_room.width - 2
    y_end = y_start + next_room.height - 2

    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            coord = (x, y)
            if coord in visible_coords:
                continue
            else:
                level.map[y][x] = ' '


def cast_ray(level, room, player, max_distance):
    visible_coords = set()
    max_dist_sq = max_distance ** 2

    for x1 in range(room.coords.x + 1, room.coords.x + room.width - 1):
        for y1 in range(room.coords.y + 1, room.coords.y + room.height - 1):
            dist_sq = (x1 - player.coords.x) ** 2 + (y1 - player.coords.y) ** 2
            if dist_sq <= max_dist_sq:
                line_coords = get_bresenham_line_coords(player.coords.x, player.coords.y, x1, y1)
                blocked = False
                for px, py in line_coords:
                    if not (0 <= py < MAP_HEIGHT and 0 <= px < MAP_WIDTH):
                        blocked = True
                        break
                    if level.map[py][px] in [curses.ACS_HLINE, curses.ACS_VLINE, curses.ACS_ULCORNER,
                                             curses.ACS_URCORNER, curses.ACS_LLCORNER, curses.ACS_LRCORNER]:
                        blocked = True
                        break
                    if level.map[py][px] == ' ':
                        blocked = True
                        break
                    visible_coords.add((px, py))
                if not blocked:
                    visible_coords.update(line_coords)
    return visible_coords
