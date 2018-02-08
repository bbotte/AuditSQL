import json

from PIL import Image
from django.contrib.auth import logout, login
from django.contrib.auth.hashers import make_password
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import FormView, RedirectView

from UserManager.models import UserAccount
from .forms import LoginForm, ChangePasswordForm


# Create your views here.

class LoginView(FormView):
    """用户登录视图， success_url登陆成功后访问的页面"""
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy('p_incep_online_sql_records')

    def form_valid(self, form):
        user = form.is_verify()
        if user is not None:
            login(self.request, user)
            # 将用户所属的组id写入到session中
            groups = UserAccount.objects.get(uid=self.request.user.uid).groupsdetail_set.all().values_list(
                'group__group_id', flat=True)
            self.request.session['groups'] = list(groups)
            return super(LoginView, self).form_valid(form)
        else:
            return render(self.request, self.template_name, {'msg': '用户名或密码错误'})


class LogoutView(RedirectView):
    """用户登出视图"""
    permanent = False
    url = reverse_lazy('p_login')

    def get(self, request, *args, **kwargs):
        logout(self.request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class IndexView(View):
    """访问首页，重定向的页面"""

    def get(self, request):
        return HttpResponseRedirect(reverse('p_incep_online_sql_records'))

class UserProfileView(View):
    def get(self, request):
        return render(request, 'profile.html')


# class UserProfileView(PaginationMixin, ListView):
#     """
#     用户详情
#     """
#     paginate_by = 6
#     context_object_name = 'user_record'
#     template_name = 'profile.html'
#
#     def get_queryset(self):
#         audit_records = UserAccount.objects.filter(proposer=self.request.user.username).order_by('-created_at')
#         return audit_records

class ChangePasswordView(View):
    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            old_password = cleaned_data['old_password']
            new_password = cleaned_data['new_password']
            verify_password = cleaned_data['verify_password']

            user = UserAccount.objects.get(uid=request.user.uid)
            if new_password == verify_password:
                if user.check_password(old_password):
                    if old_password != new_password:
                        user.password = make_password(new_password)
                        user.save()
                        context = {'errCode': '200', 'errMsg': '密码修改成功'}
                    else:
                        context = {'errCode': '400', 'errMsg': '新密码等于旧密码，请重新输入'}
                else:
                    context = {'errCode': '400', 'errMsg': '旧密码错误，请重新输入'}
            else:
                context = {'errCode': '400', 'errMsg': '密码不匹配，请重新输入'}
        else:
            error = form.errors.as_text()
            context = {'errCode': '400', 'errMsg': error}
        return HttpResponse(json.dumps(context))


class ChangePicView(View):
    def get(self, request):
        return render(request, 'userpic.html')

    def post(self, request):
        avatar_data = eval(request.POST.get('avatar_data'))

        # 保存图片到upload_to位置，并将路径写入到字段avatar_file
        photo = request.FILES.get('avatar_file')
        photo_instance = UserAccount.objects.get(uid=request.user.uid)
        photo_instance.avatar_file = photo
        photo_instance.save()

        # 获取截取图片的坐标
        x = avatar_data['x']
        y = avatar_data['y']
        w = avatar_data['width']
        h = avatar_data['height']

        # 裁剪图片
        # photo_instance.avatar_file：获取上面存储到数据库中的原始的图片（绝对路径）
        # photo_instance.avatar_file.path：获取原始图片的存储位置
        img = Image.open(photo_instance.avatar_file)
        # 按照前端传递来的坐标进行裁剪
        cropped_image = img.crop((x, y, w + x, h + y))
        # 对裁剪后的图片进行尺寸重新格式化
        resized_image = cropped_image.resize((305, 304), Image.ANTIALIAS)
        # 将裁剪后的图片替换掉原始图片，生成新的图片
        resized_image.save(photo_instance.avatar_file.path, 'PNG')

        result = {'state': 200}

        return HttpResponse(json.dumps(result))