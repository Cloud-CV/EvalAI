import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeleaderboardComponent } from './challengeleaderboard.component';
import { ChallengeService } from '../../../services/challenge.service';
import { SelectphaseComponent } from '../../../components/utility/selectphase/selectphase.component';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { HttpClientModule } from '@angular/common/http';
import { ForceloginComponent } from '../../../components/utility/forcelogin/forcelogin.component';
import { RouterTestingModule } from '@angular/router/testing';
import { EndpointsService } from '../../../services/endpoints.service';

describe('ChallengeleaderboardComponent', () => {
  let component: ChallengeleaderboardComponent;
  let fixture: ComponentFixture<ChallengeleaderboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeleaderboardComponent, SelectphaseComponent ],
      providers: [ ChallengeService, AuthService, GlobalService, ApiService, EndpointsService ],
      imports: [ HttpClientModule, RouterTestingModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeleaderboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
