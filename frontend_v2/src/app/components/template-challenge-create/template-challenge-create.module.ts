import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { ChallengeCreateComponent } from './challenge-create.component';
import { ChallengeTemplateCardComponent } from './challenge-template-card/challenge-template-card.component'

// import module
import { ChallengeCreateRoutingModule } from './challenge-create-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [
    TemplateChallengeCreateComponent
  ],
  imports: [
    CommonModule,
    ChallengeCreateRoutingModule,
    SharedModule
  ],
  exports: [
    TemplateChallengeCreateComponent
  ]
})
export class TemplateChallengeCreateModule { }