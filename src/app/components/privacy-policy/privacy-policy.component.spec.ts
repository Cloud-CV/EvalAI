import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { EndpointsService } from '../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { PrivacyPolicyComponent } from './privacy-policy.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ActivatedRoute, Router } from '@angular/router';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';


describe('PrivacyPolicyComponent', () => {
  let component: PrivacyPolicyComponent;
  let fixture: ComponentFixture<PrivacyPolicyComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PrivacyPolicyComponent, HeaderStaticComponent, FooterComponent ],
      providers: [
        GlobalService,
        AuthService,
        ApiService,
        {provide: ActivatedRoute, useValue: fakeActivatedRoute},
        {provide: Router, useClass: class { navigate = jasmine.createSpy('navigate'); }},
        EndpointsService
      ],
      imports: [ HttpClientModule, RouterTestingModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PrivacyPolicyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
