import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeparticipateComponent } from './challengeparticipate.component';
import { ChallengeService } from '../../../services/challenge.service';
import { ForceloginComponent } from '../../../components/utility/forcelogin/forcelogin.component';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { TeamlistComponent } from '../../../components/publiclists/teamlist/teamlist.component';
import { EndpointsService } from '../../../services/endpoints.service';
import { FormsModule } from '@angular/forms';

describe('ChallengeparticipateComponent', () => {
  let component: ChallengeparticipateComponent;
  let fixture: ComponentFixture<ChallengeparticipateComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengeparticipateComponent, ForceloginComponent, TeamlistComponent],
      providers: [ChallengeService, ApiService, GlobalService, AuthService, EndpointsService],
      imports: [HttpClientModule, RouterTestingModule, FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeparticipateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
