import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengesubmissionsComponent } from './challengesubmissions.component';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { WindowService } from '../../../services/window.service';
import { AuthService } from '../../../services/auth.service';
import { HttpClientModule } from '@angular/common/http';
import { ForceloginComponent } from '../../../components/utility/forcelogin/forcelogin.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChallengesubmissionsComponent', () => {
  let component: ChallengesubmissionsComponent;
  let fixture: ComponentFixture<ChallengesubmissionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengesubmissionsComponent ],
      providers: [ ChallengeService, GlobalService, AuthService, ApiService,
                   WindowService, EndpointsService ],
      imports: [ HttpClientModule, RouterTestingModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengesubmissionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
