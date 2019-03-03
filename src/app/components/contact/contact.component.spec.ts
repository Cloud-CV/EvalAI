import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ContactComponent } from './contact.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ToastComponent } from '../../components/utility/toast/toast.component';
import { InputComponent } from '../../components/utility/input/input.component';
import { MockWindowService } from '../../services/mock.window.service';
import { WindowService } from '../../services/window.service';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';

describe('ContactComponent', () => {
  let component: ContactComponent;
  let fixture: ComponentFixture<ContactComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    // Google Maps API errors out when Karma tries to load it.
    // As a result Components are not created and the tests fail.
    // Mocking the loadJS function in window service to prevent that.
    const MOCK_SERVICE = new MockWindowService(null);
    TestBed.configureTestingModule({
      imports: [ HttpClientModule, RouterTestingModule ],
      declarations: [ ContactComponent, HeaderStaticComponent, InputComponent, ToastComponent, FooterComponent ],
      providers: [
        GlobalService,
        AuthService,
        ApiService,
        {'provide': WindowService, 'useValue': MOCK_SERVICE },
        {provide: ActivatedRoute, useValue: fakeActivatedRoute},
        {provide: Router, useClass: class { navigate = jasmine.createSpy('navigate'); }},
        EndpointsService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContactComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
