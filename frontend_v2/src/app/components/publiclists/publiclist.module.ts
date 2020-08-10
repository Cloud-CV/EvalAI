import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// import components
import { PubliclistsComponent } from './publiclists.component';

// import routes
import { PubliclistRoutingModule, TeamlistsRoutingModule } from './publiclist-routing.module';

// import Module
import { ChallengelistModule } from './challengelist/challengelist.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [PubliclistsComponent],
  imports: [CommonModule, PubliclistRoutingModule, ChallengelistModule, SharedModule],
  exports: [ChallengelistModule, PubliclistsComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class PubliclistModule {}

@NgModule({
  declarations: [],
  imports: [CommonModule, TeamlistsRoutingModule, PubliclistModule, SharedModule],
  exports: [PubliclistModule],
})
export class TeamlistsModule {}
