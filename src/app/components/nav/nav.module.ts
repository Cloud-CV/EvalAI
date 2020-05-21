import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

// import component
import { FooterComponent } from './footer/footer.component';
import { HeaderStaticComponent } from './header-static/header-static.component';

// import module
import { UtilityModule } from '../utility/utility.module';

@NgModule({
declarations: [
  FooterComponent,
  HeaderStaticComponent
],
imports: [
  CommonModule,
  FormsModule,
  RouterModule,
  UtilityModule
],
exports: [
  FooterComponent,
  HeaderStaticComponent,
  UtilityModule
],
schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})

export class NavModule {}
