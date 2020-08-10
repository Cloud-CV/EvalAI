import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengecardComponent } from './challengecard.component';
import { GlobalService } from '../../../../services/global.service';
import { ApiService } from '../../../../services/api.service';
import { AuthService } from '../../../../services/auth.service';
import { EndpointsService } from '../../../../services/endpoints.service';
import { ChallengeService } from '../../../../services/challenge.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

describe('ChallengecardComponent', () => {
  let component: ChallengecardComponent;
  let fixture: ComponentFixture<ChallengecardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule, RouterTestingModule],
      declarations: [ChallengecardComponent],
      providers: [GlobalService, ApiService, AuthService, ChallengeService, EndpointsService],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengecardComponent);
    component = fixture.componentInstance;
    component.challenge = {
      id: 1,
      title: 'Anthony Challenge',
      short_description: 'Architecto reiciendis',
      description: 'Ipsa sit exercitationem ',
      terms_and_conditions: 'Officiis dicta debitis expedita corrupti.',
      submission_guidelines: 'Totam ipsa debitis ',
      evaluation_details: 'Dolorem consequatur odio quos',
      image: 'https://evalai.s3.amazonaws.com/media/logos/vqa.png',
      start_date: '2017-12-03T03:38:12.655908Z',
      end_date: '2019-07-26T03:38:12.655934Z',
      creator: {
        id: 1,
        team_name: 'New Travischester Host Team',
        created_by: 'host',
      },
      published: true,
      enable_forum: true,
      anonymous_leaderboard: false,
      is_active: true,
      approved_by_admin: true,
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
