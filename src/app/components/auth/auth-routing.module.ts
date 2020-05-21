import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthComponent } from './auth.component';
import { LoginComponent } from './login/login.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { ResetPasswordConfirmComponent } from './reset-password-confirm/reset-password-confirm.component';
import { SignupComponent } from './signup/signup.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';

const routes: Routes = [
  {
    path: 'auth',
    component: AuthComponent,
    children: [
      {path: '', redirectTo: 'login', pathMatch: 'full'},
      {path: 'login', component: LoginComponent},
      {path: 'reset-password', component: ResetPasswordComponent},
      {path: 'reset-password/confirm/:user_id/:reset_token', component: ResetPasswordConfirmComponent},
      {path: 'signup', component: SignupComponent},
      {path: 'verify-email/:token', component: VerifyEmailComponent},
      {path: '**', redirectTo: 'login'}
    ]
  },
];
@NgModule({
  imports: [ RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AuthRoutingModule {}
