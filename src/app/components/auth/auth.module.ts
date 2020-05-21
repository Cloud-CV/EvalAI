import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

// import components
import { LoginComponent } from './login/login.component';
import { SignupComponent } from './signup/signup.component';
import { ResetPasswordConfirmComponent } from './reset-password-confirm/reset-password-confirm.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { AuthComponent } from './auth.component';

// import modules
import { AuthRoutingModule } from './auth-routing.module';
import { NavModule } from '../nav/nav.module';

// import services
import { AuthService } from '../../services/auth.service';


@NgModule({
  declarations: [
    LoginComponent,
    SignupComponent,
    ResetPasswordConfirmComponent,
    ResetPasswordComponent,
    VerifyEmailComponent,
    AuthComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    AuthRoutingModule,
    FormsModule,
    NavModule
  ],
  exports: [
    LoginComponent,
    SignupComponent,
    ResetPasswordConfirmComponent,
    ResetPasswordComponent,
    VerifyEmailComponent,
    AuthComponent,
    NavModule
  ],
  providers: [
    AuthService
  ]
})
export class AuthModule { }
