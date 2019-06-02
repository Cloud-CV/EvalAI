import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeCreateComponent } from './challenge-create.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';
import {Router, Routes} from '@angular/router';
import {NotFoundComponent} from '../not-found/not-found.component';

const routes: Routes = [
  {
    path: 'challenge-create',
    component: ChallengeCreateComponent,
  },
  {
    path: '404',
    component: NotFoundComponent
  },
  {
    path: '**',
    redirectTo: '/404',
    pathMatch: 'full'
  }
];

describe('ChallengecreateComponent', () => {
  let component: ChallengeCreateComponent;
  let fixture: ComponentFixture<ChallengeCreateComponent>;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChallengeCreateComponent, HeaderStaticComponent, FooterComponent, NotFoundComponent ],
      schemas: [ NO_ERRORS_SCHEMA ],
      imports: [ RouterTestingModule.withRoutes(routes), HttpClientModule ],
      providers: [ GlobalService, AuthService, ApiService, ChallengeService, EndpointsService ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(ChallengeCreateComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.ngZone.run(() => {
      router.navigate(['/challenge-create/']).then(() => {
        fixture.detectChanges();
        expect(component).toBeTruthy();
      });
    });
  });
});
