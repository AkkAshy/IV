# from rest_framework import serializers
# from .models import University, Building, Faculty, Floor, Room, RoomHistory, FacultyHistory
# from django.db import transaction

# class UniversitySerializer(serializers.ModelSerializer):

#     class Meta:
#         model = University
#         fields = ['id', 'name', 'address', 'logo']

# class BuildingSerializer(serializers.ModelSerializer):
#     university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())

#     class Meta:
#         model = Building
#         fields = ['id', 'name', 'address', 'photo', 'university']

# class FacultySerializer(serializers.ModelSerializer):
#     building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

#     class Meta:
#         model = Faculty
#         fields = ['id', 'name', 'photo', 'building', 'floor']

# class FloorSerializer(serializers.ModelSerializer):
#     building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

#     class Meta:
#         model = Floor
#         fields = ['id', 'number', 'description', 'building']



# class RoomSerializer(serializers.ModelSerializer):
#     floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())
#     building = serializers.PrimaryKeyRelatedField(
#         queryset=Building.objects.all(),
#         required=True
#     )
#     qr_code_url = serializers.SerializerMethodField()
#     derived_from = serializers.PrimaryKeyRelatedField(
#         queryset=Room.objects.all(),
#         allow_null=True,
#         required=False
#     )
#     derived_from_display = serializers.SerializerMethodField()

#     class Meta:
#         model = Room
#         fields = [
#             'id',
#             'number',
#             'name',
#             'is_special',
#             'photo',
#             'qr_code',
#             'qr_code_url',
#             'floor',
#             'building',
#             'derived_from',
#             'derived_from_display'
#         ]
#         read_only_fields = ['qr_code', 'qr_code_url']

#     def get_qr_code_url(self, obj):
#         if obj.qr_code and hasattr(obj.qr_code, 'url'):
#             request = self.context.get('request')
#             if request:
#                 return request.build_absolute_uri(obj.qr_code.url)
#         return None

#     def get_derived_from_display(self, obj):
#         if obj.derived_from:
#             return str(obj.derived_from)
#         return None

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         if instance.floor:
#             data['building'] = instance.floor.building.id
#         return data



# class RoomHistorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = RoomHistory
#         fields = ['id', 'room', 'action', 'timestamp', 'description']



# class RoomSplitSerializer(serializers.Serializer):
#     new_rooms = serializers.ListField(
#         child=serializers.DictField(
#             child=serializers.CharField(),
#             required=True
#         ),
#         required=True,
#         help_text="List of new rooms, e.g., [{'number': '101A'}, {'number': '101B'}]"
#     )

#     def validate_new_rooms(self, value):
#         room = self.context['room']
#         errors = []
#         for i, new_room in enumerate(value):
#             number = new_room.get('number')
#             if not number:
#                 errors.append(f"Room {i+1}: number is required")
#             elif Room.objects.filter(floor=room.floor, number=number).exists():
#                 errors.append(f"Room {i+1}: number {number} already exists on this floor")
#         if errors:
#             raise serializers.ValidationError(errors)
#         return value

#     @transaction.atomic
#     def save(self):
#         room = self.context['room']
#         new_rooms = []
#         for new_room_data in self.validated_data['new_rooms']:
#             new_room = Room(
#                 number=new_room_data['number'],
#                 name=f"{room.name} (split)" if room.name else "",
#                 building=room.building,
#                 floor=room.floor,
#                 is_special=room.is_special,
#                 derived_from=room
#             )
#             new_room.save()  # QR-код создаётся автоматически
#             RoomHistory.objects.create(
#                 room=new_room,
#                 action='Split',
#                 description=f'Split from room {room.number} (ID: {room.id})'
#             )
#             new_rooms.append(new_room)

#         room.is_special = False
#         room.save()
#         RoomHistory.objects.create(
#             room=room,
#             action='Split',
#             description=f'Split into rooms: {", ".join(r["number"] for r in self.validated_data["new_rooms"])}'
#         )
#         return new_rooms

# class RoomMergeSerializer(serializers.Serializer):
#     room_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         required=True,
#         min_length=2,
#         help_text="List of room IDs to merge"
#     )
#     number = serializers.CharField(required=True)
#     floor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Floor.objects.all(),
#         required=True
#     )
#     building_id = serializers.PrimaryKeyRelatedField(
#         queryset=Building.objects.all(),
#         required=True
#     )

#     def validate(self, data):
#         room_ids = data['room_ids']
#         number = data['number']
#         floor = data['floor_id']
#         building = data['building_id']
#         if Room.objects.filter(floor=floor, number=number).exists():
#             raise serializers.ValidationError(f"Room {number} already exists on this floor")
#         if not Room.objects.filter(id__in=room_ids).count() == len(room_ids):
#             raise serializers.ValidationError("Some room IDs are invalid")
#         if floor.building != building:
#             raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
#         return data

#     @transaction.atomic
#     def save(self):
#         rooms = Room.objects.filter(id__in=self.validated_data['room_ids'])
#         new_room = Room(
#             number=self.validated_data['number'],
#             building=self.validated_data['building_id'],
#             floor=self.validated_data['floor_id'],
#             is_special=any(room.is_special for room in rooms)
#         )
#         new_room.save()

#         room_numbers = [room.number for room in rooms]
#         for room in rooms:
#             RoomHistory.objects.create(
#                 room=room,
#                 action='Merged',
#                 description=f'Merged into room {new_room.number} (ID: {new_room.id})'
#             )
#             room.derived_from = new_room
#             room.is_special = False
#             room.save()

#         RoomHistory.objects.create(
#             room=new_room,
#             action='Merged',
#             description=f'Merged from rooms: {", ".join(room_numbers)}'
#         )
#         return new_room

# class RoomMoveSerializer(serializers.Serializer):
#     floor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Floor.objects.all(),
#         required=True
#     )
#     building_id = serializers.PrimaryKeyRelatedField(
#         queryset=Building.objects.all(),
#         required=True
#     )

#     def validate(self, data):
#         room = self.context['room']
#         floor = data['floor_id']
#         building = data['building_id']
#         if Room.objects.filter(floor=floor, number=room.number).exclude(id=room.id).exists():
#             raise serializers.ValidationError(f"Room {room.number} already exists on this floor")
#         if floor.building != building:
#             raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
#         return data

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         old_floor = instance.floor.number
#         old_building = instance.building.name
#         instance.floor = validated_data['floor_id']
#         instance.building = validated_data['building_id']
#         instance.save()

#         RoomHistory.objects.create(
#             room=instance,
#             action='Transferred',
#             description=f'Transferred from floor {old_floor}, building {old_building} to floor {instance.floor.number}, building {instance.building.name}'
#         )
#         return instance

# class NewFacultySerializer(serializers.Serializer):
#     name = serializers.CharField(required=True)
#     floor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Floor.objects.all(),
#         required=True
#     )

#     def validate(self, data):
#         faculty = self.context.get('faculty')
#         floor = data.get('floor_id')
#         if faculty and floor.building != faculty.building:
#             raise serializers.ValidationError(
#                 f"Floor {floor.number} does not belong to building {faculty.building.name}"
#             )
#         return data

# class FacultySplitSerializer(serializers.Serializer):
#     new_faculties = serializers.ListField(
#         child=NewFacultySerializer(),
#         required=True,
#         help_text="List of new faculties, e.g., [{'name': 'Faculty A', 'floor_id': 1}, {'name': 'Faculty B', 'floor_id': 2}]"
#     )

#     def validate_new_faculties(self, value):
#         faculty = self.context['faculty']
#         errors = []
#         for i, new_faculty in enumerate(value):
#             name = new_faculty.get('name')
#             if not name:
#                 errors.append(f"Faculty {i+1}: name is required")
#             elif Faculty.objects.filter(building=faculty.building, name=name).exists():
#                 errors.append(f"Faculty {i+1}: name {name} already exists in this building")
#         if errors:
#             raise serializers.ValidationError(errors)
#         return value

#     @transaction.atomic
#     def save(self):
#         faculty = self.context['faculty']
#         new_faculties = []
#         for new_faculty_data in self.validated_data['new_faculties']:
#             new_faculty = Faculty(
#                 name=new_faculty_data['name'],
#                 building=faculty.building,
#                 floor=new_faculty_data['floor_id']
#             )
#             new_faculty.save()
#             FacultyHistory.objects.create(
#                 faculty=new_faculty,
#                 action='Split',
#                 description=f'Split from faculty {faculty.name} (ID: {faculty.id})'
#             )
#             new_faculties.append(new_faculty)

#         FacultyHistory.objects.create(
#             faculty=faculty,
#             action='Split',
#             description=f'Split into faculties: {", ".join(f["name"] for f in self.validated_data["new_faculties"])}'
#         )
#         return new_faculties

# class FacultyMergeSerializer(serializers.Serializer):
#     faculty_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         required=True,
#         min_length=2,
#         help_text="List of faculty IDs to merge"
#     )
#     name = serializers.CharField(required=True)
#     building_id = serializers.PrimaryKeyRelatedField(
#         queryset=Building.objects.all(),
#         required=True
#     )
#     floor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Floor.objects.all(),
#         required=True
#     )

#     def validate(self, data):
#         faculty_ids = data['faculty_ids']
#         name = data['name']
#         building = data['building_id']
#         floor = data['floor_id']
#         if Faculty.objects.filter(building=building, name=name).exists():
#             raise serializers.ValidationError(f"Faculty {name} already exists in this building")
#         if not Faculty.objects.filter(id__in=faculty_ids).count() == len(faculty_ids):
#             raise serializers.ValidationError("Some faculty IDs are invalid")
#         if floor.building != building:
#             raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
#         return data

#     @transaction.atomic
#     def save(self):
#         faculties = Faculty.objects.filter(id__in=self.validated_data['faculty_ids'])
#         new_faculty = Faculty(
#             name=self.validated_data['name'],
#             building=self.validated_data['building_id'],
#             floor=self.validated_data['floor_id']
#         )
#         new_faculty.save()

#         faculty_names = [faculty.name for faculty in faculties]
#         for faculty in faculties:
#             FacultyHistory.objects.create(
#                 faculty=faculty,
#                 action='Merged',
#                 description=f'Merged into faculty {new_faculty.name} (ID: {new_faculty.id})'
#             )
#             faculty.save()

#         FacultyHistory.objects.create(
#             faculty=new_faculty,
#             action='Merged',
#             description=f'Merged from faculties: {", ".join(faculty_names)}'
#         )
#         return new_faculty

# class FacultyMoveSerializer(serializers.Serializer):
#     floor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Floor.objects.all(),
#         required=True
#     )
#     building_id = serializers.PrimaryKeyRelatedField(
#         queryset=Building.objects.all(),
#         required=True
#     )

#     def validate(self, data):
#         faculty = self.context['faculty']
#         building = data['building_id']
#         floor = data['floor_id']
#         if Faculty.objects.filter(building=building, name=faculty.name).exclude(id=faculty.id).exists():
#             raise serializers.ValidationError(f"Faculty {faculty.name} already exists in this building")
#         if floor.building != building:
#             raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
#         return data

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         old_building = instance.building.name
#         old_floor = instance.floor.number if instance.floor else "None"
#         instance.floor = validated_data['floor_id']
#         instance.building = validated_data['building_id']
#         instance.save()

#         FacultyHistory.objects.create(
#             faculty=instance,
#             action='Transferred',
#             description=f'Transferred from building {old_building}, floor {old_floor} to building {instance.building.name}, floor {instance.floor.number}'
#         )
#         return instance


from rest_framework import serializers
from .models import University, Building, Faculty, Floor, Room, RoomHistory, FacultyHistory
from django.db import transaction


class UniversitySerializer(serializers.ModelSerializer):

    class Meta:
        model = University
        fields = ['id', 'name', 'address', 'logo']

class BuildingSerializer(serializers.ModelSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())

    class Meta:
        model = Building
        fields = ['id', 'name', 'address', 'photo', 'university']

class FacultySerializer(serializers.ModelSerializer):
    building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

    class Meta:
        model = Faculty
        fields = ['id', 'name', 'photo', 'building', 'floor']

class FloorSerializer(serializers.ModelSerializer):
    building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

    class Meta:
        model = Floor
        fields = ['id', 'number', 'description', 'building']



class RoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all())
    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        required=True
    )
    qr_code_url = serializers.SerializerMethodField()
    derived_from = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        allow_null=True,
        required=False
    )
    derived_from_display = serializers.SerializerMethodField()



    class Meta:
        model = Room
        fields = [
            'id',
            'number',
            'name',
            'is_special',
            'photo',
            'qr_code',
            'qr_code_url',
            'floor',
            'building',
            'derived_from',
            'derived_from_display',
            'author',
        ]
        read_only_fields = ['qr_code', 'qr_code_url', 'equipments']

    def get_qr_code_url(self, obj):
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
            return f"http://localhost:8000{obj.qr_code.url}"
        return None

    def get_derived_from_display(self, obj):
        if obj.derived_from:
            return str(obj.derived_from)
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.floor:
            data['building'] = instance.floor.building.id
        return data



class RoomHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomHistory
        fields = ['id', 'room', 'action', 'timestamp', 'description']



class RoomSplitSerializer(serializers.Serializer):
    new_rooms = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=True
        ),
        required=True,
        help_text="List of new rooms, e.g., [{'number': '101A'}, {'number': '101B'}]"
    )

    def validate_new_rooms(self, value):
        room = self.context['room']
        errors = []
        for i, new_room in enumerate(value):
            number = new_room.get('number')
            if not number:
                errors.append(f"Room {i+1}: number is required")
            elif Room.objects.filter(floor=room.floor, number=number).exists():
                errors.append(f"Room {i+1}: number {number} already exists on this floor")
        if errors:
            raise serializers.ValidationError(errors)
        return value

    @transaction.atomic
    def save(self):
        room = self.context['room']
        new_rooms = []
        for new_room_data in self.validated_data['new_rooms']:
            new_room = Room(
                number=new_room_data['number'],
                name=f"{room.name} (split)" if room.name else "",
                building=room.building,
                floor=room.floor,
                is_special=room.is_special,
                derived_from=room
            )
            new_room.save()  # QR-код создаётся автоматически
            RoomHistory.objects.create(
                room=new_room,
                action='Split',
                description=f'Split from room {room.number} (ID: {room.id})'
            )
            new_rooms.append(new_room)

        room.is_special = False
        room.save()
        RoomHistory.objects.create(
            room=room,
            action='Split',
            description=f'Split into rooms: {", ".join(r["number"] for r in self.validated_data["new_rooms"])}'
        )
        return new_rooms

class RoomMergeSerializer(serializers.Serializer):
    room_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=2,
        help_text="List of room IDs to merge"
    )
    number = serializers.CharField(required=True)
    floor_id = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.all(),
        required=True
    )
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        required=True
    )

    def validate(self, data):
        room_ids = data['room_ids']
        number = data['number']
        floor = data['floor_id']
        building = data['building_id']
        if Room.objects.filter(floor=floor, number=number).exists():
            raise serializers.ValidationError(f"Room {number} already exists on this floor")
        if not Room.objects.filter(id__in=room_ids).count() == len(room_ids):
            raise serializers.ValidationError("Some room IDs are invalid")
        if floor.building != building:
            raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
        return data

    @transaction.atomic
    def save(self):
        rooms = Room.objects.filter(id__in=self.validated_data['room_ids'])
        new_room = Room(
            number=self.validated_data['number'],
            building=self.validated_data['building_id'],
            floor=self.validated_data['floor_id'],
            is_special=any(room.is_special for room in rooms)
        )
        new_room.save()

        room_numbers = [room.number for room in rooms]
        for room in rooms:
            RoomHistory.objects.create(
                room=room,
                action='Merged',
                description=f'Merged into room {new_room.number} (ID: {new_room.id})'
            )
            room.derived_from = new_room
            room.is_special = False
            room.save()

        RoomHistory.objects.create(
            room=new_room,
            action='Merged',
            description=f'Merged from rooms: {", ".join(room_numbers)}'
        )
        return new_room

class RoomMoveSerializer(serializers.Serializer):
    floor_id = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.all(),
        required=True
    )
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        required=True
    )

    def validate(self, data):
        room = self.context['room']
        floor = data['floor_id']
        building = data['building_id']
        if Room.objects.filter(floor=floor, number=room.number).exclude(id=room.id).exists():
            raise serializers.ValidationError(f"Room {room.number} already exists on this floor")
        if floor.building != building:
            raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        old_floor = instance.floor.number
        old_building = instance.building.name
        instance.floor = validated_data['floor_id']
        instance.building = validated_data['building_id']
        instance.save()

        RoomHistory.objects.create(
            room=instance,
            action='Transferred',
            description=f'Transferred from floor {old_floor}, building {old_building} to floor {instance.floor.number}, building {instance.building.name}'
        )
        return instance

class NewFacultySerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    floor_id = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.all(),
        required=True
    )

    def validate(self, data):
        faculty = self.context.get('faculty')
        floor = data.get('floor_id')
        if faculty and floor.building != faculty.building:
            raise serializers.ValidationError(
                f"Floor {floor.number} does not belong to building {faculty.building.name}"
            )
        return data

class FacultySplitSerializer(serializers.Serializer):
    new_faculties = serializers.ListField(
        child=NewFacultySerializer(),
        required=True,
        help_text="List of new faculties, e.g., [{'name': 'Faculty A', 'floor_id': 1}, {'name': 'Faculty B', 'floor_id': 2}]"
    )

    def validate_new_faculties(self, value):
        faculty = self.context['faculty']
        errors = []
        for i, new_faculty in enumerate(value):
            name = new_faculty.get('name')
            if not name:
                errors.append(f"Faculty {i+1}: name is required")
            elif Faculty.objects.filter(building=faculty.building, name=name).exists():
                errors.append(f"Faculty {i+1}: name {name} already exists in this building")
        if errors:
            raise serializers.ValidationError(errors)
        return value

    @transaction.atomic
    def save(self):
        faculty = self.context['faculty']
        new_faculties = []
        for new_faculty_data in self.validated_data['new_faculties']:
            new_faculty = Faculty(
                name=new_faculty_data['name'],
                building=faculty.building,
                floor=new_faculty_data['floor_id']
            )
            new_faculty.save()
            FacultyHistory.objects.create(
                faculty=new_faculty,
                action='Split',
                description=f'Split from faculty {faculty.name} (ID: {faculty.id})'
            )
            new_faculties.append(new_faculty)

        FacultyHistory.objects.create(
            faculty=faculty,
            action='Split',
            description=f'Split into faculties: {", ".join(f["name"] for f in self.validated_data["new_faculties"])}'
        )
        return new_faculties

class FacultyMergeSerializer(serializers.Serializer):
    faculty_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=2,
        help_text="List of faculty IDs to merge"
    )
    name = serializers.CharField(required=True)
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        required=True
    )
    floor_id = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.all(),
        required=True
    )

    def validate(self, data):
        faculty_ids = data['faculty_ids']
        name = data['name']
        building = data['building_id']
        floor = data['floor_id']
        if Faculty.objects.filter(building=building, name=name).exists():
            raise serializers.ValidationError(f"Faculty {name} already exists in this building")
        if not Faculty.objects.filter(id__in=faculty_ids).count() == len(faculty_ids):
            raise serializers.ValidationError("Some faculty IDs are invalid")
        if floor.building != building:
            raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
        return data

    @transaction.atomic
    def save(self):
        faculties = Faculty.objects.filter(id__in=self.validated_data['faculty_ids'])
        new_faculty = Faculty(
            name=self.validated_data['name'],
            building=self.validated_data['building_id'],
            floor=self.validated_data['floor_id']
        )
        new_faculty.save()

        faculty_names = [faculty.name for faculty in faculties]
        for faculty in faculties:
            FacultyHistory.objects.create(
                faculty=faculty,
                action='Merged',
                description=f'Merged into faculty {new_faculty.name} (ID: {new_faculty.id})'
            )
            faculty.save()

        FacultyHistory.objects.create(
            faculty=new_faculty,
            action='Merged',
            description=f'Merged from faculties: {", ".join(faculty_names)}'
        )
        return new_faculty

class FacultyMoveSerializer(serializers.Serializer):
    floor_id = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.all(),
        required=True
    )
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        required=True
    )

    def validate(self, data):
        faculty = self.context['faculty']
        building = data['building_id']
        floor = data['floor_id']
        if Faculty.objects.filter(building=building, name=faculty.name).exclude(id=faculty.id).exists():
            raise serializers.ValidationError(f"Faculty {faculty.name} already exists in this building")
        if floor.building != building:
            raise serializers.ValidationError(f"Floor {floor.number} does not belong to building {building.name}")
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        old_building = instance.building.name
        old_floor = instance.floor.number if instance.floor else "None"
        instance.floor = validated_data['floor_id']
        instance.building = validated_data['building_id']
        instance.save()

        FacultyHistory.objects.create(
            faculty=instance,
            action='Transferred',
            description=f'Transferred from building {old_building}, floor {old_floor} to building {instance.building.name}, floor {instance.floor.number}'
        )
        return instance



from django.urls import reverse

class RoomLinkSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'number', 'building', 'link']

    def get_link(self, obj):
        request = self.context.get('request')
        base_url = request.build_absolute_uri(reverse('room-detail', args=[obj.id]))
        return f"{base_url}?building={obj.building.id}"