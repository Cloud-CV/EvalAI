import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// import component
import { AuthComponent } from './auth.component';
import { LoginComponent } from './login/login.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { ResetPasswordConfirmComponent } from './reset-password-confirm/reset-password-confirm.component';
import { SignupComponent } from './signup/signup.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';

const routes: Routes = [
  {
    path: '',
    component: AuthComponent,
    children: [
      { path: '', redirectTo: 'login', pathMatch: 'full' },
      { path: 'login', component: LoginComponent },
      { path: 'reset-password', component: ResetPasswordComponent },
      { path: 'api/password/reset/confirm/:user_id/:reset_token', component: ResetPasswordConfirmComponent },
      { path: 'signup', component: SignupComponent },
      { path: 'verify-email/:token', component: VerifyEmailComponent },
      { path: '**', redirectTo: 'login' },
    ],
  },
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AuthRoutingModule {}
