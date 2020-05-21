import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

// import components
import { ChallengelistComponent } from './challengelist/challengelist.component';
import { ChallengecardComponent } from './challengelist/challengecard/challengecard.component';
import { TeamcardComponent } from './teamlist/teamcard/teamcard.component';
import { TeamlistComponent } from './teamlist/teamlist.component';
import { PubliclistsComponent } from './publiclists.component';

// import services
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { ChallengeService } from '../../services/challenge.service';

// import routes
import { PubliclistRoutingModule } from './publiclist-routing.module';

// import Module
import { NavModule } from '../nav/nav.module';

@NgModule({
  declarations: [
    ChallengelistComponent,
    ChallengecardComponent,
    TeamcardComponent,
    TeamlistComponent,
    PubliclistsComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    PubliclistRoutingModule,
    NavModule
  ],
  exports: [
    ChallengelistComponent,
    ChallengecardComponent,
    TeamcardComponent,
    TeamlistComponent,
    PubliclistsComponent,
    NavModule
  ],
  providers: [
    ApiService,
    GlobalService,
    AuthService,
    ChallengeService
  ],
  schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})
export class PubliclistModule {}
