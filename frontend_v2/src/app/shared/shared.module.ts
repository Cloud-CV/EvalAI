import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// import directive
import { PasswordMismatchValidatorDirective } from '../Directives/password.validator';
import { EmailValidatorDirective } from '../Directives/email.validator';
import { LazyImageDirective } from '../Directives/image.lazyload';

// import component
import { HeaderStaticComponent } from '../components/nav/header-static/header-static.component';
import { FooterComponent } from '../components/nav/footer/footer.component';
import { NotFoundComponent } from '../components/not-found/not-found.component';

// import module
import { UtilityModule } from '../components/utility/utility.module';

@NgModule({
  declarations: [
    PasswordMismatchValidatorDirective,
    EmailValidatorDirective,
    LazyImageDirective,
    HeaderStaticComponent,
    FooterComponent,
    NotFoundComponent,
  ],
  imports: [CommonModule, RouterModule, FormsModule, UtilityModule],
  exports: [
    PasswordMismatchValidatorDirective,
    EmailValidatorDirective,
    LazyImageDirective,
    CommonModule,
    RouterModule,
    FormsModule,
    HeaderStaticComponent,
    FooterComponent,
    UtilityModule,
    NotFoundComponent,
  ],
})
export class SharedModule {}
