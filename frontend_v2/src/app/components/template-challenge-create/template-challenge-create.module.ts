import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDatepickerModule, MatInputModule, MatNativeDateModule } from '@angular/material';

// import component
import { TemplateChallengeCreateComponent } from './template-challenge-create.component';

// import module
import { TemplateChallengeCreateRoutingModule } from './template-challenge-create-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [TemplateChallengeCreateComponent],
  imports: [
    CommonModule,
    TemplateChallengeCreateRoutingModule,
    SharedModule,
    MatDatepickerModule,
    MatInputModule,
    MatNativeDateModule,
  ],
  exports: [TemplateChallengeCreateComponent],
})
export class TemplateChallengeCreateModule {}
