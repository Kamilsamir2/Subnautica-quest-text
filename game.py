import json
import os
import random
import sys
from typing import Dict, List, Any

class Game:
    def __init__(self, data_file: str = "data.json"):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(base_path, data_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.locations = self.data['locations']
        self.current_location = "capsule"
        self.inventory = []

        self.health = 100
        self.hunger = 100
        self.thirst = 100
        self.oxygen = 100

        self.fire_extinguished = False
        self.crate_opened = False
        self.cave_completed = False
        self.leviathan_alive = True
        self.leviathan_first_attack = False
        self.cave_state = None
        self.medkit_taken = False
        self.cave_titan_taken = False
        self.capsule_state_timer = 0
        self.running = True
        self.last_underwater_location = "underwater"

    #  Вспомогательные методы

    def apply_stats_cost(self, location: str):
        """Тратит показатели в зависимости от локации (уменьшенный расход)."""
        self.hunger -= 3
        self.thirst -= 5
        underwater_locs = [
            "underwater", "cave_entrance", "cave_path", "cave_end", "wreck",
            "leviathan_zone", "leviathan_fight"
        ]
        if location in underwater_locs:
            self.oxygen -= 5

        if self.hunger <= 0:
            print("Вы умерли от голода.")
            self.running = False
        elif self.thirst <= 0:
            print("Вы умерли от жажды.")
            self.running = False
        elif self.oxygen <= 0 and location in underwater_locs:
            print("Вы задохнулись под водой.")
            self.running = False

    def restore_oxygen_if_possible(self):
        loc = self.locations.get(self.current_location)
        if loc and loc.get("surface", False):
            self.oxygen = 100

    def show_stats(self):
        print(f"\n--- HP {self.health} | Голод {self.hunger} | Жажда {self.thirst} | Кислород {self.oxygen} ---")

    #  Сохранение / загрузка

    def save_game(self, filename: str = "savegame.json"):
        save_data = {
            "current_location": self.current_location,
            "inventory": self.inventory,
            "health": self.health,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "oxygen": self.oxygen,
            "fire_extinguished": self.fire_extinguished,
            "crate_opened": self.crate_opened,
            "cave_completed": self.cave_completed,
            "leviathan_alive": self.leviathan_alive,
            "leviathan_first_attack": self.leviathan_first_attack,
            "cave_state": self.cave_state,
            "medkit_taken": self.medkit_taken,
            "cave_titan_taken": self.cave_titan_taken,
            "capsule_state_timer": self.capsule_state_timer,
            "last_underwater_location": self.last_underwater_location
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print("Игра сохранена.")

    def load_game(self, filename: str = "savegame.json"):
        if not os.path.exists(filename):
            print("Файл сохранения не найден.")
            return
        with open(filename, 'r', encoding='utf-8') as f:
            save_data = json.load(f)

        self.current_location = save_data["current_location"]
        self.inventory = save_data["inventory"]
        self.health = save_data["health"]
        self.hunger = save_data["hunger"]
        self.thirst = save_data["thirst"]
        self.oxygen = save_data["oxygen"]
        self.fire_extinguished = save_data.get("fire_extinguished", False)
        self.crate_opened = save_data.get("crate_opened", False)
        self.cave_completed = save_data.get("cave_completed", False)
        self.leviathan_alive = save_data.get("leviathan_alive", True)
        self.leviathan_first_attack = save_data.get("leviathan_first_attack", False)
        self.cave_state = save_data.get("cave_state", None)
        self.medkit_taken = save_data.get("medkit_taken", False)
        self.cave_titan_taken = save_data.get("cave_titan_taken", False)
        self.capsule_state_timer = save_data.get("capsule_state_timer", 0)
        self.last_underwater_location = save_data.get("last_underwater_location", "underwater")
        print("Игра загружена.")

    #  Инвентарь и предметы

    def inventory_menu(self):
        while True:
            print("\n=== Инвентарь ===")
            if not self.inventory:
                print("Пусто")
                return
            for i, item in enumerate(self.inventory, 1):
                print(f"{i}. {item}")
            print("0. Назад")
            choice = input("> ")
            if choice == "0":
                return
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.inventory):
                    self.inspect_item(self.inventory[idx])
                else:
                    print("Неверный номер.")
            except ValueError:
                print("Ошибка ввода.")

    def inspect_item(self, item_name: str):
        item = self.data["items"].get(item_name)
        if not item:
            print("Предмет не найден.")
            return
        print("\n" + item["description"])
        if item.get("usable"):
            print("\n1. Использовать")
            print("0. Назад")
            choice = input("> ")
            if choice == "1":
                self.use_item(item_name)

    def use_item(self, item_name: str):
        item = self.data["items"].get(item_name)
        if not item:
            return
        effect = item.get("effect")
        if effect == "drink":
            self.thirst = min(100, self.thirst + 40)
            self.inventory.remove(item_name)
            print("Вы выпили воду.")
        elif effect == "eat":
            self.hunger = min(100, self.hunger + 40)
            self.inventory.remove(item_name)
            print("Вы съели паёк.")
        elif effect == "heal":
            self.health = 100
            self.inventory.remove(item_name)
            print("Здоровье полностью восстановлено.")
        elif effect == "salvage":
            if "металлолом" in self.inventory:
                self.inventory.remove("металлолом")
                self.inventory.append("титан")
                print("Металлолом переработан в титан.")
            else:
                print("Нет металлолома.")
        else:
            print("Этот предмет нельзя использовать.")

    def craft_knife(self):
        if "нож" in self.inventory:
            print("У вас уже есть нож.")
            return
        if self.inventory.count("титан") < 2:
            print("Нужно 2 титана.")
            return
        for _ in range(2):
            self.inventory.remove("титан")
        self.inventory.append("нож")
        print("Вы изготовили нож.")

    def search_wreck(self):
        roll = random.randint(1, 100)
        if roll <= 35:
            self.inventory.append("вода")
            print("Вы нашли воду.")
        elif roll <= 70:
            self.inventory.append("еда")
            print("Вы нашли еду.")
        elif roll <= 90:
            self.inventory.append("металлолом")
            print("Вы нашли металлолом.")
        else:
            print("Вдали появляется огромный силуэт...")
            self.current_location = "leviathan_zone"

    #  Встреча с Жнецом (двухэтапная атака)

    def leviathan_encounter(self):
        if not self.leviathan_alive:
            print("Здесь плавает туша убитого Жнеца.")
            return

        if not self.leviathan_first_attack:
            # Первая атака
            print("Жнец замечает вас и наносит первый удар!")
            self.health -= 90
            if self.health <= 0:
                print("Челюсти смыкаются вокруг вас. Вы погибли.")
                self.running = False
                return
            print("Вы чудом выжили, но Жнец разъярён. Он готовится ко второму удару.")
            self.leviathan_first_attack = True
            # Остаёмся в зоне, чтобы игрок мог вылечиться
            return

        else:
            # Вторая атака
            print("Жнец бросается на вас снова!")
            self.health -= 50
            if self.health <= 0:
                print("Второй удар оказывается смертельным. Вы погибли.")
                self.running = False
                return
            print("Вы выдержали вторую атаку. Теперь ваш черёд!")

            if "нож" in self.inventory:
                self.current_location = "leviathan_fight"
            else:
                print("У вас нет ножа, приходится отступать.")
                self.current_location = "wreck"
            # Сбросим флаг для следующей встречи (на случай сохранения/загрузки)
            self.leviathan_first_attack = False

    def attack_leviathan(self):
        if "нож" not in self.inventory:
            print("Нужен нож.")
            return
        print("Вы вонзаете нож в глаз Жнеца.")
        self.leviathan_alive = False
        self.current_location = "victory"

    #  Обработка действий

    def process_action(self, action: Dict[str, Any]) -> bool:
        action_id = action.get("id")
        custom = action.get("custom_logic")

        if action_id == "take_tablet" and "планшет" in self.inventory:
            print("Планшет уже у вас.")
            return True
        if action_id == "take_extinguisher" and "огнетушитель" in self.inventory:
            print("Огнетушитель уже у вас.")
            return True
        if action_id == "take_medkit" and self.medkit_taken:
            print("Аптечка уже взята.")
            return True
        if action_id == "take_titan" and self.cave_titan_taken:
            print("Титан уже взят.")
            return True

        if custom:
            if custom == "extinguish_fire":
                if not self.fire_extinguished:
                    self.fire_extinguished = True
                    self.capsule_state_timer = 1
                    print(action.get("result_text", "Пожар потушен."))
                else:
                    print("Пожар уже потушен.")
                return True

            elif custom == "check_cave_available":
                if self.cave_completed:
                    print("Вы уже исследовали пещеру, там больше нечего делать.")
                    self.current_location = "underwater"
                else:
                    self.current_location = action["next_location"]
                return True

            elif custom == "init_cave_puzzle":
                if "планшет" not in self.inventory:
                    print("У вас нет подсказки. Вы блуждаете в темноте...")
                    print("Вы заблудились и наткнулись на рыбу-камикадзе. Взрыв! Вы погибли.")
                    return False
                self.cave_state = {"step": 0, "sequence": ["left", "right", "left"]}
                print(action.get("result_text", "Вы начинаете двигаться по пещере..."))
                self.current_location = action.get("next_location", "cave_path")
                return True

            elif custom == "dive_back":
                self.current_location = self.last_underwater_location
                print("Вы ныряете обратно в глубину.")
                return True

            elif custom == "cave_choice":
                chosen = None
                if action_id == "go_left":
                    chosen = "left"
                elif action_id == "go_right":
                    chosen = "right"
                elif action_id == "go_straight":
                    chosen = "straight"

                if self.cave_state is None or self.cave_state["step"] >= len(self.cave_state["sequence"]):
                    print("Странно, пещера уже пройдена.")
                    self.current_location = "cave_entrance"
                    return True

                step = self.cave_state["step"]
                sequence = self.cave_state["sequence"]
                if chosen == sequence[step]:
                    self.cave_state["step"] += 1
                    if self.cave_state["step"] == len(sequence):
                        print("Вы прошли опасный участок! Рыба-камикадзе проплыла мимо.")
                        self.current_location = "air_pocket"
                        self.cave_state = None
                        return True
                    else:
                        print("Пока безопасно, продолжайте.")
                        self.current_location = "cave_path"
                        return True
                else:
                    print("Неверный путь! Рыба-камикадзе взрывается рядом. Вы погибли.")
                    return False

            elif custom == "reset_cave":
                self.cave_state = None
                print(action.get("result_text", "Вы возвращаетесь."))
                self.current_location = action["next_location"]
                return True

            elif custom == "complete_cave":
                self.cave_completed = True
                self.current_location = action["next_location"]
                return True

            elif custom == "search_wreck":
                self.search_wreck()
                return True

            elif custom == "leviathan_encounter":
                self.leviathan_encounter()
                return True

            elif custom == "attack_leviathan":
                self.attack_leviathan()
                return True

            elif custom == "craft_knife":
                self.craft_knife()
                return True

            elif custom == "restore_oxygen":
                self.oxygen = 100
                print("Вы восстановили запас кислорода.")
                return True

            elif custom == "end_game":
                self.running = False
                print("Игра завершена. Спасибо за игру!")
                return True

        if action.get("action_type") == "save":
            if self.current_location == "capsule":
                self.save_game()
            else:
                print("Сохраниться можно только в спасательной капсуле.")
            return True

        if "effects" in action:
            effects = action["effects"]
            if "inventory_add" in effects:
                items = effects["inventory_add"]
                if isinstance(items, list):
                    for it in items:
                        if it in ["планшет", "огнетушитель"] and it in self.inventory:
                            print(f"{it} уже есть в инвентаре.")
                            continue
                        if it == "аптечка" and self.medkit_taken:
                            print("Аптечка уже была взята.")
                            continue
                        if it == "титан" and self.cave_titan_taken:
                            print("Титан уже был взят.")
                            continue
                        self.inventory.append(it)
                        print(f"Предмет '{it}' добавлен в инвентарь.")
                        if it == "аптечка":
                            self.medkit_taken = True
                        if it == "титан" and action_id == "take_titan":
                            self.cave_titan_taken = True
                else:
                    it = items
                    if it in ["планшет", "огнетушитель"] and it in self.inventory:
                        print(f"{it} уже есть в инвентаре.")
                    elif it == "аптечка" and self.medkit_taken:
                        print("Аптечка уже была взята.")
                    elif it == "титан" and self.cave_titan_taken:
                        print("Титан уже был взят.")
                    else:
                        self.inventory.append(it)
                        print(f"Предмет '{it}' добавлен в инвентарь.")
                        if it == "аптечка":
                            self.medkit_taken = True
                        if it == "титан" and action_id == "take_titan":
                            self.cave_titan_taken = True

            if "flag_set" in effects:
                setattr(self, effects["flag_set"], True)

        if "result_text" in action:
            print(action["result_text"])

        if "next_location" in action:
            next_loc = action["next_location"]
            if next_loc == "water_surface" and self.current_location != "water_surface":
                self.last_underwater_location = self.current_location
            self.current_location = next_loc
            if self.current_location == "air_pocket":
                self.oxygen = 100
                print("Вы обнаружили воздушный карман и восстанавливаете дыхание.")
            if action_id == "leave_end" and self.current_location == "underwater":
                self.cave_completed = True

        return True

    #  Отображение локации

    def show_location(self):
        loc_key = self.current_location
        if self.current_location == "cave_entrance" and self.cave_completed:
            loc_key = "cave_entrance_completed"

        loc = self.locations.get(loc_key)
        if not loc:
            print("Ошибка: локация не найдена.")
            return []

        print("\n" + "=" * 50)
        print(f"=== {loc['name']} ===")

        if loc_key == "capsule" and isinstance(loc.get("description"), dict):
            if self.capsule_state_timer == 0:
                print(loc["description"]["fire"])
            elif self.capsule_state_timer == 1:
                print(loc["description"]["safe"])
            else:
                print(loc["description"]["normal"])
        else:
            print(loc.get("description", "Нет описания."))

        if self.inventory:
            print(f"\nИнвентарь: {', '.join(self.inventory)}")
        self.show_stats()
        print("\nЧто делать?")

        available_actions = []
        for act in loc['actions']:
            skip = False
            if "requires" in act:
                reqs = act["requires"]
                if not isinstance(reqs, list):
                    reqs = [reqs]
                for req in reqs:
                    if "item" in req:
                        item = req["item"]
                        required_state = req.get("state", True)
                        has_item = item in self.inventory
                        if has_item != required_state:
                            skip = True
                            break
                    if "flag" in req:
                        flag_val = getattr(self, req["flag"], False)
                        required_state = req.get("state", True)
                        if flag_val != required_state:
                            skip = True
                            break
            if act.get("id") == "extinguish_fire" and self.fire_extinguished:
                skip = True
            if act.get("id") == "open_crate" and self.crate_opened:
                skip = True
            if act.get("id") == "take_tablet" and "планшет" in self.inventory:
                skip = True
            if act.get("id") == "take_extinguisher" and "огнетушитель" in self.inventory:
                skip = True
            if act.get("id") == "take_medkit" and self.medkit_taken:
                skip = True
            if act.get("id") == "take_titan" and self.cave_titan_taken:
                skip = True

            if not skip:
                available_actions.append(act)

        for i, act in enumerate(available_actions, 1):
            print(f"{i}. {act['text']}")
        print("99. Инвентарь")
        print("0. Выйти из игры")
        return available_actions

    #  Главный цикл

    def run(self):
        print("Добро пожаловать в текстовый квест 'Subnautica на минималках'!")

        while self.running:
            self.restore_oxygen_if_possible()

            if self.current_location == "capsule" and self.capsule_state_timer == 1:
                self.capsule_state_timer = 2

            if self.health <= 0:
                print("Вы погибли.")
                break
            if self.hunger <= 0 or self.thirst <= 0:
                print("Вы погибли из-за нехватки ресурсов.")
                break
            if self.oxygen <= 0 and self.current_location in ["underwater", "cave_entrance", "cave_path", "cave_end", "wreck", "leviathan_zone", "leviathan_fight"]:
                print("Вы задохнулись под водой.")
                break

            available_actions = self.show_location()
            choice = input("> ").strip().lower()

            if choice == "0" or choice == "выход":
                print("Выход из игры. До свидания!")
                break
            elif choice == "сохранить":
                if self.current_location == "capsule":
                    self.save_game()
                else:
                    print("Сохраниться можно только в спасательной капсуле.")
                continue
            elif choice == "загрузить":
                self.load_game()
                continue
            elif choice == "99":
                self.inventory_menu()
                continue
            else:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(available_actions):
                        action = available_actions[idx - 1]
                        if action.get("action_type") != "save":
                            self.apply_stats_cost(self.current_location)
                            if not self.running:
                                break
                        if not self.process_action(action):
                            print("Игра окончена. Вы погибли.")
                            self.running = False
                            break
                    else:
                        print("Неверный номер действия.")
                except ValueError:
                    print("Неизвестная команда.")

        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    game = Game()
    game.run()