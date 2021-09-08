import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// import components
import { FeaturedChallengesComponent } from './featured-challenges/featured-challenges.component';
import { HomemainComponent } from './homemain/homemain.component';
import { PartnersComponent } from './partners/partners.component';
import { RulesComponent } from './rules/rules.component';
import { HomeComponent } from './home.component';

// import module
import { SharedModule } from '../../shared/shared.module';
import { HomeRoutingModule } from './home-routing.module';

@NgModule({
  declarations: [
    HomeComponent,
    PartnersComponent,
    RulesComponent,
    HomemainComponent,
    FeaturedChallengesComponent,
  ],
  imports: [CommonModule, HomeRoutingModule, SharedModule],
  exports: [
    HomeComponent,
    PartnersComponent,
    RulesComponent,
    HomemainComponent,
    FeaturedChallengesComponent,
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class HomeModule {}
