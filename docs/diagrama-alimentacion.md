classDiagram
%% CAPA DE DOMINIO (Tu lógica pura)
class FeedingSession {
+start()
+stop()
}

    class IFeedingStrategy {
        <<Interface>>
        +get_plc_configuration() MachineConfiguration
    }

    class ManualStrategy {
        +get_plc_configuration()
    }

    class IFeedingMachine {
        <<Interface>>
        +send_configuration(config)
    }

    class MachineConfiguration {
        <<DTO>>
        +mode
        +speed
        +target
    }

    %% CAPA DE INFRAESTRUCTURA (El mundo real)
    class SimulatedFeedingMachine {
        +send_configuration(config)
        -memory_dict
    }

    class ModbusFeedingMachine {
        +send_configuration(config)
        -modbus_client
    }

    %% RELACIONES
    FeedingSession --> IFeedingStrategy : Usa (El Cerebro)
    FeedingSession --> IFeedingMachine : Usa (El Brazo)
    FeedingSession ..> MachineConfiguration : Pasa datos

    ManualStrategy ..|> IFeedingStrategy : Implementa

    SimulatedFeedingMachine ..|> IFeedingMachine : Implementa
    ModbusFeedingMachine ..|> IFeedingMachine : Implementa

classDiagram
%% CAPA DE DOMINIO (Tu lógica pura)
class FeedingSession {
+start()
+stop()
}

    class IFeedingStrategy {
        <<Interface>>
        +get_plc_configuration() MachineConfiguration
    }

    class ManualStrategy {
        +get_plc_configuration()
    }

    class IFeedingMachine {
        <<Interface>>
        +send_configuration(config)
    }

    class MachineConfiguration {
        <<DTO>>
        +mode
        +speed
        +target
    }

    %% CAPA DE INFRAESTRUCTURA (El mundo real)
    class SimulatedFeedingMachine {
        +send_configuration(config)
        -memory_dict
    }

    class ModbusFeedingMachine {
        +send_configuration(config)
        -modbus_client
    }

    %% RELACIONES
    FeedingSession --> IFeedingStrategy : Usa (El Cerebro)
    FeedingSession --> IFeedingMachine : Usa (El Brazo)
    FeedingSession ..> MachineConfiguration : Pasa datos

    ManualStrategy ..|> IFeedingStrategy : Implementa

    SimulatedFeedingMachine ..|> IFeedingMachine : Implementa
    ModbusFeedingMachine ..|> IFeedingMachine : Implementa
