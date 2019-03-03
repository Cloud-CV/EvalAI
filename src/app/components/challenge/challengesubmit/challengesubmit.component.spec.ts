import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengesubmitComponent } from './challengesubmit.component';
import { ChallengeService } from '../../../services/challenge.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { HttpClientModule } from '@angular/common/http';
import { ForceloginComponent } from '../../../components/utility/forcelogin/forcelogin.component';
import { RouterTestingModule } from '@angular/router/testing';
import { EndpointsService } from '../../../services/endpoints.service';

describe('ChallengesubmitComponent', () => {
  let component: ChallengesubmitComponent;
  let fixture: ComponentFixture<ChallengesubmitComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengesubmitComponent ],
      providers: [ ChallengeService, GlobalService, AuthService, ApiService, EndpointsService ],
      imports: [ HttpClientModule, RouterTestingModule],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengesubmitComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
