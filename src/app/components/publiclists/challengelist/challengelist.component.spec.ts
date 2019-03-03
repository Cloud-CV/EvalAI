import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ChallengelistComponent } from './challengelist.component';
import { CardlistComponent } from '../../../components/utility/cardlist/cardlist.component';
import { ChallengecardComponent } from './challengecard/challengecard.component';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { ForceloginComponent } from '../../../components/utility/forcelogin/forcelogin.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChallengelistComponent', () => {
  let component: ChallengelistComponent;
  let fixture: ComponentFixture<ChallengelistComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ HttpClientModule, RouterTestingModule ],
      declarations: [ ChallengelistComponent,
                      CardlistComponent,
                      ChallengecardComponent,
                      ForceloginComponent ],
      providers: [ GlobalService,
                   ApiService,
                   AuthService,
                   EndpointsService ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengelistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
