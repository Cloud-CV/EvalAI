import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import components
import { LoginComponent } from './login/login.component';
import { SignupComponent } from './signup/signup.component';
import { ResetPasswordConfirmComponent } from './reset-password-confirm/reset-password-confirm.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { AuthComponent } from './auth.component';

// import service
import { AuthService } from '../../services/auth.service';

// import module
import { SharedModule } from '../../shared/shared.module';
import { AuthRoutingModule } from './auth-routing.module';

@NgModule({
  declarations: [
    LoginComponent,
    SignupComponent,
    ResetPasswordConfirmComponent,
    ResetPasswordComponent,
    VerifyEmailComponent,
    AuthComponent,
  ],
  imports: [CommonModule, AuthRoutingModule, SharedModule],
  exports: [
    AuthComponent,
    LoginComponent,
    SignupComponent,
    ResetPasswordComponent,
    ResetPasswordConfirmComponent,
    VerifyEmailComponent,
  ],
  providers: [AuthService],
})
export class AuthModule {}
