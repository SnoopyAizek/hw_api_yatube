import base64

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from posts.models import Post, Comment, Group, Follow, User
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class PostSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Post
        fields = ('id', 'author', 'text', 'pub_date', 'image', 'group')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'created', 'post')
        read_only_fields = ('post',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'title', 'slug', 'description')


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    following = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(queryset=Follow.objects.all(), fields=('user', 'following'),
                                    message='Вы уже подписывались на этого автора')
        ]

    def to_internal_value(self, data):
        following = data.get('following')
        following_pk = get_object_or_404(User, username=following)
        data.update({'following': following_pk.pk})
        return super().to_internal_value(data)

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError('Подписка на cамого себя невозможна')
        return data
