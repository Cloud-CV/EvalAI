import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgxTwitterTimelineModule } from 'ngx-twitter-timeline';

// import components
import { FeaturedChallengesComponent } from './featured-challenges/featured-challenges.component';
import { HomemainComponent } from './homemain/homemain.component';
import { PartnersComponent } from './partners/partners.component';
import { RulesComponent } from './rules/rules.component';
import { TestimonialsComponent } from './testimonials/testimonials.component';
import { TwitterFeedComponent } from './twitter-feed/twitter-feed.component';
import { HomeComponent } from './home.component';

// import module
import { SharedModule } from '../../shared/shared.module';
import { HomeRoutingModule } from './home-routing.module';

@NgModule({
  declarations: [
    HomeComponent,
    TwitterFeedComponent,
    PartnersComponent,
    RulesComponent,
    TestimonialsComponent,
    HomemainComponent,
    FeaturedChallengesComponent,
  ],
  imports: [CommonModule, HomeRoutingModule, NgxTwitterTimelineModule, SharedModule],
  exports: [
    HomeComponent,
    TwitterFeedComponent,
    PartnersComponent,
    RulesComponent,
    TestimonialsComponent,
    HomemainComponent,
    FeaturedChallengesComponent,
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class HomeModule {}
