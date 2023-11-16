from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import CustomUser
from accounts.forms import ProfileForm, SignupUserForm
from django.shortcuts import render, redirect
from allauth.account import views
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string


class SignupView(views.SignupView):
    template_name = 'accounts/signup.html'
    form_class = SignupUserForm

    def get_initial(self):
        """フォームの初期値を返す"""
        # 親クラスを呼び出してデフォルトの初期値辞書を得る
        initial = self.initial.copy()

        # 初期値辞書を返す
        return initial
    

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        zipCode = self.request.POST.get("郵便番号")
        address = self.request.POST.get("住所")

        
        self.form = form
        self.object = form.save()
        self.object.zipCode = zipCode
        self.object.address = address
        self.object.save()

        login(self.request, self.object)
        
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):


        context = {
            "first_name": self.form.cleaned_data["first_name"],
            "last_name": self.form.cleaned_data["last_name"],
            "email": self.form.cleaned_data["email"],
            "kind": self.form.cleaned_data["kind"],
            "tel": self.form.cleaned_data["tel"],
            "gender": self.form.cleaned_data["gender"],
            "age": self.form.cleaned_data["age"],
            "zipCode": self.object.zipCode,
            "address": self.object.address
        }

        messages.success(
        self.request, '「{}」として登録完了しました。'.format(self.object))

        subject = "ハコフィットへの会員登録が完了しました"
        message = render_to_string("accounts/registration_mail.txt", context)
        from_email = 'hakofit.reserve@gmail.com'  # 送信者
        recipient_list = [self.form.cleaned_data['email'], "s.seisaku.co@icloud.com"]  # 宛先リスト(to)
        send_mail(subject, message, from_email, recipient_list)
        self.request.session['user_id'] = self.object.id


class LoginView(views.LoginView):
    template_name = 'accounts/login.html'


class LogoutView(views.LogoutView):
    template_name = 'accounts/logout.html'

    def post(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.logout()
        return redirect('/')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)

        return render(request, 'accounts/profile.html', {
            'user_data': user_data,
        })


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = CustomUser.objects.get(id=request.user.id)
        form = ProfileForm(
            request.POST or None,
            initial={
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'address': user_data.address,
                'tel': user_data.tel
            }
        )

        return render(request, 'accounts/profile_edit.html', {
            'form': form
        })

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST or None)
        if form.is_valid():
            user_data = CustomUser.objects.get(id=request.user.id)
            user_data.first_name = form.cleaned_data['first_name']
            user_data.last_name = form.cleaned_data['last_name']
            user_data.address = form.cleaned_data['address']
            user_data.tel = form.cleaned_data['tel']
            user_data.save()
            return redirect('profile')

        return render(request, 'accounts/profile.html', {
            'form': form
        })
